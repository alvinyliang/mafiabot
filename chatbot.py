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
import Queue

class TwitchBot(irc.bot.SingleServerIRCBot):
    game_exists = False
    game_is_full = False
    game_started = False
    player_count = 0
    wait_queue = Queue.Queue()


    def __init__(self, username, client_id, token, channel):
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel

        self.players = {}
        self.total_players = 2

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
            c.privmsg(self.channel, r['display_name'] + ' is currently playing ' + r['game'])

        elif cmd == "startmafia":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()

            self.start_mafia(c, e)
        elif cmd == "vote":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json() 
        elif cmd == "status":
            sender = e.source.split("!")[0]
            c.privmsg(self.channel, "/w " + sender + str(self.players.keys()))
        else:
            c.privmsg(self.channel, "Did not understand command: " + cmd)

        # Poll the API the get the current status of the stream
        #elif cmd == "title":
        #    url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        #    headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        #    r = requests.get(url, headers=headers).json()
        #    c.privmsg(self.channel, r['display_name'] + ' channel title is currently ' + r['status'])

        # The command was not recognized

    def start_mafia(self, c, e):
        #add to players list

        sender = e.source.split("!")[0]

        if not self.game_exists:
            self.players[sender] = 1
            self.player_count = 1
            self.game_exists = True
            
            # TODO: get user. self.players.append(username)

            message = "Game created by " + sender + ", waiting for enough players to join. (" + str(self.player_count) + "/" + str(self.total_players) + ")"
            
            c.privmsg(self.channel, message)


        elif self.game_is_full:
            # TODO: get user. self.wait_queue.put(username)
            message = "Current game is full. You are in the waiting queue for the next game."
            c.privmsg(self.channel, message)
        else:

            if str(sender) not in self.players:

                self.player_count += 1
                self.players[sender] = 1

                # TODO: get user. self.players.append(username)
                message = sender + ' has been added to the game. (' + str(self.player_count) + "/" + str(self.total_players) + ")"

                # TODO: get user. message = username + ' has been added to the game lobby. '
                c.privmsg(self.channel, message)

                
                if self.player_count == self.total_players:
                    self.game_is_full = True
                    self.game_started = True
                    message = "There are enough players now, game starting!"
                    c.privmsg(self.channel, message)
                    self.start_gameplay(c, e)
            else:
                c.privmsg(self.channel, "Cannot add to game, already in game")


    class Player(object):
        role = 0
        messages = ''
        tokens = []

        def __init__(self, name):
            self.name = name

        def get_role(self):
            if self.role == 1:
                return 'a mafioso'
            return 'a villager'''

    def start_gameplay(self, c, e):
        print self.players

        nums = [x for x in range(8)]
        random.shuffle(nums)

        villagers_count = 6
        mafia_count = 2


        sender = e.source.split("!")[0]

        i = 0
        for key, value in self.players.iteritems():
            self.players[key] = i
            i += 1

        i = 0
        
        print self.players.keys()

        for key, value in self.players.iteritems():
            if value == 0:
                message = "/w " + key + " you are mafia."
                c.privmsg(self.channel, message)

            else:
                message = "/w " + key + " you are villager."
                c.privmsg(self.channel, message)
            i += 1

        day = 0
        victim = None
        
        while mafia_count > 0 and (villagers_count - mafia_count) > mafia_count:
            message = 'Day {} begins.'.format(day)
            c.privmsg(self.channel, message)


            if day > 0:

                del self.players[victim]


                message = 'Today is Day {}.'.format(day) + 'Last night, {} was killed.'.format(victim) \
                          + 'These players are still alive: {}'.format(', '.join(self.players.keys()))
                c.privmsg(self.channel, message)

                # Don't go to night if a win condition's been met.
                if mafia_count == 0 and (villagers_count - mafia_count) == mafia_count:
                    break

                # START TODO
                num_votes = 0
                votes = []
                if cmd == "vote" and day != 0:
                    num_votes += 1
                    #votes[p.name] += 1
                    #message = '{} has voted to kill {}'.format(p.name, )
                    # TO-DO: need to get user name and who to kill
                    c.privmsg(self.channel, message)

                elif cmd == "abstain" and day != 0:
                    num_votes += 1
                    # message = '{} has voted to kill no one'.format(p.name)
                    # TO-DO: need to get user name
                    c.privmsg(self.channel, message)

                max = 0
                killed = None
                for vote in votes:
                    if votes[vote] > max:
                        max = votes[vote]
                        killed = vote

                # The most voted player is killed, ties broken randomly
                if killed is not None:
                    message = 'The town has killed {}'.format(p.name) + 'They were {}.'.format(killed.get_role())
                    c.privmsg(self.channel, message)
                else:
                    message = 'The town did not kill anyone today.'
                    c.privmsg(self.channel, message)

            # Don't go to night if a win condition's been met.
            if mafia_count == 0 and (villagers_count - mafia_count) == mafia_count:
                break

            # NIGHT ACTION
            # Mafia decides on a victim
            mafia = []
            mafia.append(self.players.get(0))
            mafia.append(self.players.get(1))


            for m in mafia:
                for key, value in self.players.iteritems(){
                    self.players[key] = (value, i)
                    if m != None:
                        c.privmsg(self.channel, "/w " + m + " " + str(name,  + " is the target")
                    }
                # whisper who to kill, save it

            #message = 'The mafia decides to kill {}'.format(p.name)
            # END TODO
            #c.privmsg(self.channel, message)



            day += 1




        if mafia_count > 0:
            message = 'MAFIA VICTORY'

        else:
            message = 'VILLAGE VICTORY'


        #c.privmsg(self.channel, message)
       # self.prepare_next_game(c)
        """

    def prepare_next_game(self, c):
        if wait_queue.empty():
            self.game_exists = False
            self.game_is_full = False
            self.game_started = False
            self.player_count = 0
            self.players = []
        else:
            self.players = []
            self.game_exists = True
            while not wait_queue.empty():
                self.player_count += 1
                self.players.append(wait_queue.get())

                if player_count == total_players:
                    break

            message = 'These players have been added to the game from wait queue {}'.format(', '.join(self.players))
            c.privmsg(self.channel, message)
            if player_count == total_players:
                self.game_is_full = True
                message = "There are enough players now, game starting!"
                c.privmsg(self.channel, message)
                self.start_gameplay(c)
            else:
                message = "Game created, waiting for enough players to join."
                c.privmsg(self.channel, message)
        """

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
