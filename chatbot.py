'''
Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
'''

import sys
import irc.bot
import requests
import random

class TwitchBot(irc.bot.SingleServerIRCBot):
    total_players = 3
    game_exists = False
    game_is_full = False
    player_count = 0
    players = ['Alice', 'Bob', 'Charlie', 'David', 'Edgar', 'Frank', 'Gina', 'Harold']


    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        # Get the channel id, we will need this for v5 API calls
        url = 'https://api.twitch.tv/kraken/users?login=' + channel
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']

        # Create IRC bot connection
        server = 'irc.chat.twitch.tv'
        port = 6667
        print 'Connecting to ' + server + ' on port ' + str(port) + '...'
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)
        

    def on_welcome(self, c, e):
        print 'Joining ' + self.channel

        # You must request specific capabilities before you can use them
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)

    def on_pubmsg(self, c, e):
        # If a chat message starts with an exclamation point, try to run it as a command
        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            print 'Received command: ' + cmd
            self.do_command(e, cmd)
        return

    def do_command(self, e, cmd):
        c = self.connection

        # Poll the API to get current game.
        if cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['display_name'] + ' is currently playing a game')
            #c.privmsg(self.channel, r['display_name'] + ' is currently playing ' + r['game'])

        elif cmd == "startmafia":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            self.start_mafia(c, r)

        # Poll the API the get the current status of the stream
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['display_name'] + ' channel title is currently ' + r['status'])

        # Provide basic information to viewers for specific commands
        elif cmd == "raffle":
            message = "This is an example bot, replace this text with your raffle text."
            c.privmsg(self.channel, message)
        elif cmd == "schedule":
            message = "This is an example bot, replace this text with your schedule text."            
            c.privmsg(self.channel, message)

        # The command was not recognized
        else:
            c.privmsg(self.channel, "Did not understand command: " + cmd)

    def start_mafia(self, c, r):
        if not self.game_exists:
            self.player_count = 1
            self.game_exists = True
            #self.players.append(r['display_name'])

            message = "Game created, waiting for enough players to join."
            c.privmsg(self.channel, message)
        elif self.game_is_full:
            self.wait_queue.append(r['display_name'])
            message = "Current game is full. You are in the waiting queue for the next game."
            c.privmsg(self.channel, message)
        else:
            self.player_count += 1
            #self.players.append(r['display_name'])

            message = r['display_name'] + ' has been added to the game. '
            c.privmsg(self.channel, message)
            if self.player_count == self.total_players:
                self.game_is_full = True
                message = "There are enough players now, game starting!"
                c.privmsg(self.channel, message)
                self.start_gameplay(c)


    class Player(object):
        role = 0
        messages = ''

        def __init__(self, name):
            self.name = name

        def get_role(self):
            if self.role == 1:
                return 'a mafioso'
            return 'a villager'

    def start_gameplay(self, c):
        nums = [x for x in range(8)]
        random.shuffle(nums)
        villagers = []
        mafia = []

        for num in nums:
            player = self.Player(self.players[num])
            if num == 0 or num == 1:
                mafia.append(player)
            else:
                villagers.append(player)

        print(len(mafia))
        print(len(villagers))
        message = 'The players playing: {}'.format(', '.join(self.players))
        c.privmsg(self.channel, message)

        day = 0
        suspect, victim = None, None

        '''while False and (len(villagers) - len(mafia)) > len(mafia):
            message = 'Day {} begins.'.format(day)
            c.privmsg(self.channel, message)

            # random turn order each day

            if day == 0:
                for v in villagers:
                    # send message via whisper. "Today is Day 0. No voting will occur today. Beware of the mafia tonight"

                for m in mafia:
                    # send message via whisper. "You are part of the mafia. Your ally is: " get other mafia
            else:
                message = 'Today is Day {}.'.format(day) + 'Last night, {} was killed.'.format(victim) +
                          'These players are still alive: {}'.format(', '.join(p.name for p in players))'''


def main():
    if len(sys.argv) != 5:
        print("Usage: twitchbot <username> <client id> <token> <channel>")
        sys.exit(1)

    username  = sys.argv[1]
    client_id = sys.argv[2]
    token     = sys.argv[3]
    channel   = sys.argv[4]

    bot = TwitchBot(username, client_id, token, channel)
    bot.start()

if __name__ == "__main__":
    main()
