import sys
import getopt
from slacker import Slacker, Error

DEBUG = True


# Print usage
def usage(name):
    print("Usage: {} -a apikey -c channel -o namefile -f filterfile [-hpwb]\n".format(name))


# Get Slack channel ID
def get_slack_channel_id(s, c):
    response = s.channels.list()
    channels = [d for d in response.body['channels'] if d['name'] == c]
    if not len(channels):
        print("Cannot find channel")
        sys.exit(1)
    assert len(channels) == 1
    channel_id = channels[0]['id']
    return channel_id


# Main method
def main():

    # Default values
    apikey = "apikey.txt"
    channel = ""
    oname_file = ""
    filter_file = ""
    do_plan = False
    filter_dict = {}

    # Get command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:c:o:f:h:p', ['apikey=',
                                                                 'channel=',
                                                                 'oname=',
                                                                 'filter=',
                                                                 'help',
                                                                 'plan'])
    except getopt.GetoptError:
        usage(sys.argv[0])
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(sys.argv[0])
            sys.exit(2)
        elif opt in ('-p', '--plan'):
            do_plan = True
        elif opt in ('-a', '--apikey'):
            apikey = arg
        elif opt in ('-c', '--channel'):
            channel = arg.strip('\'"')
        elif opt in ('-o', '--oname'):
            oname_file = arg
        elif opt in ('-f', '--filter'):
            filter_file = arg
        else:
            usage(sys.argv[0])
            sys.exit(2)

    if DEBUG:
        print("apikey - {}".format(apikey))
        print("channel - {}".format(channel))
        print("oname_file - {}".format(oname_file))
        print("filter_file - {}".format(filter_file))

    # Load API key from apikey.txt
    try:
        with open(apikey, "r") as f:
            api_key = f.read().strip()
            assert api_key
    except IOError:
        print("Cannot find {} or other reading error".format(apikey))
        sys.exit(1)
    except AssertionError:
        print("Empty API key")
        sys.exit(1)
    else:
        slack = Slacker(api_key)

    # Read in filter file if specified
    if filter_file:
        try:
            with open(filter_file, "r") as f:
                for line in f:
                    u_name, f_name = line.strip().split(' ', 1)
                    filter_dict[u_name] = f_name
        except IOError:
            print("Cannot find {} or other reading error".format(filter_file))

    if DEBUG:
        print(filter_dict)

    # Get output file handle if specified
    if oname_file:
        try:
            ofile_h = open(oname_file, "w")
        except IOError:
            print("Cannot write file {}, or other writing error".format(oname_file))
            sys.exit(1)

    # Get channel id from name
    channel_id = get_slack_channel_id(slack, channel)

    # Get users list
    response = slack.users.list()
    users = [(u['id'], u['name'], u['profile']['real_name'], u['is_bot'],
              u['deleted'], u['is_restricted'], u['is_ultra_restricted']) for u in response.body['members']]

    # Invite users to slack channel
    for user_id, user_name, real_name, is_bot, is_deleted, is_restricted, is_ultra_restricted in users:
        if oname_file:
            ofile_h.write("{} {}\n".format(user_name, real_name))
        try:
            if not is_deleted and \
                    not is_restricted and \
                    not is_ultra_restricted and \
                    not is_bot and \
                    user_name not in filter_dict:
                if not do_plan:
                    slack.channels.invite(channel_id, user_id)
                else:
                    print("PLAN: slack.channels.invite({}, {}) -> {} {} {} {} {} {}".format(channel_id, user_id,
                                                                                            user_name, real_name,
                                                                                            is_bot, is_deleted,
                                                                                            is_restricted,
                                                                                            is_ultra_restricted))
        except Error as e:
            code = e.args[0]
            if code == "already_in_channel":
                print("{} is already in the channel".format(user_name))
            elif code in ('cant_invite_self', 'cant_invite', 'user_is_ultra_restricted'):
                print("Skipping user {} ('{}')".format(user_name, code))
            else:
                print("UNKNOWN ERROR: unable to invite {} to channel {} with error code {}".format(user_name,
                                                                                                   channel, code))


if __name__ == '__main__':
    main()
