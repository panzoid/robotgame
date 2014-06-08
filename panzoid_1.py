import rg
import time
import random

# version 1.0.0

class Robot:
    def __init__(self):
        self.turn = -1
        self.firstActTimeLimitMilli = 1500
        self.subsequentActTimeLimitMilli = 300
        self.my_bots_history = []
        self.enemy_bots_history = []
        
        self.max_attack = rg.settings.attack_range[1]
    def act(self, game):
        self.game = game
        if self.isFirstActOfTurn():
            self.giveOrders()
         
        return self.followOrder()
        
    def isFirstActOfTurn(self):
        if self.game.turn != self.turn:
            self.turn = self.game.turn
            return True
        else:
            return False
    
    # The first bot that acts at the start of a new turn is the leader and gives orders that it and other bots will follow.
    def giveOrders(self):
        # Initialize and populate our dicts of bots
        self.my_bots = {}
        self.enemy_bots = {}
        # Set of locations where we can't move due to another robot
        self.blocked_move_locs = set()
        
        for loc, bot in self.game.robots.iteritems():
            self.blocked_move_locs.add(loc)
            if bot.player_id == self.player_id:
                self.my_bots[loc] = bot
            else:
                self.enemy_bots[loc] = bot
        
        for loc, my_bot in self.my_bots.iteritems():
            self.my_bots[loc]['order'] = self.giveOrder(my_bot)
            
        self.my_bots_history.append(self.my_bots)
        self.enemy_bots_history.append(self.enemy_bots)
        
        
    def followOrder(self):
        return self.my_bots[self.location]['order']
    
    def giveOrder(self, my_bot):
        nearbyEnemies = self.getNearbyEnemies(my_bot.location, 1)
        if len(nearbyEnemies) > 0:
            # try to flee to safe location
            for open_loc in self.getNearbyOpenLocations(my_bot.location):
                # Found an open safe location, move there
                if len(self.getNearbyEnemies(open_loc, 1)) == 0:
                    return self.move(my_bot, open_loc)
            # bot won't survive this turn, suicide
            if len(nearbyEnemies) * self.max_attack > my_bot.hp:
                return self.suicide(my_bot)
            # bot will survive, attack enemy with lowest hp
            else:
                return self.attack(my_bot, sorted(nearbyEnemies.values(), key=lambda x: x.hp)[0].location)
        # bot is safe without moving. Try to preemptively attack or just move towards center
        else:
            nearbyEnemies = self.getNearbyEnemies(my_bot.location, 2)
            # there are enemies two spaces away, see if we can preemptively attack the spot they'll move into
            if len(nearbyEnemies) > 0:
                (preemptiveAttackBool, attack_loc) = self.canPreemptivelyAttack(my_bot, nearbyEnemies)
                if preemptiveAttackBool:
                    return self.attack(my_bot, attack_loc)

            return self.moveTowards(my_bot, rg.CENTER_POINT)
            
    def canPreemptivelyAttack(self, my_bot, enemy_bots_dict):
        nearbyOpenLocs = self.getNearbyOpenLocations(my_bot.location)
        enemy_bots_list = sorted(enemy_bots_dict.values(), key=lambda x: x.hp)
        
        for enemy_bot in enemy_bots_list:
            (x0, y0) = my_bot.location
            (x, y) = enemy_bot.location
            x_diff, y_diff = x - x0, y - y0

            loc_y = (x0, y0 + cmp(y_diff, 0))
            loc_x = (x0 + cmp(x_diff, 0), y0)
            
            if loc_y in nearbyOpenLocs:
                return (True, loc_y)
            if loc_x in nearbyOpenLocs:
                return (True, loc_x)
                
        return (False, None)
        
    
    # Moves the bot towards the loc, going around any obstacles. If bot is already at loc then just guard.
    def moveTowards(self, my_bot, loc):
        if my_bot.location == loc:
            return self.guard(my_bot)
        
        locs = self.getNearbyOpenLocations(my_bot.location)
        # if bot has nowhere to move then just guard
        if len(locs) == 0:
            return self.guard(my_bot)
        
        locs = sorted(locs, key=lambda x: rg.dist(x, loc))
        return self.move(my_bot, locs[0])
    
    # Returns open locations sorted by distance that are adjacent to destination location
    # filter out spawn points by default
    def getNearbyOpenLocations(self, loc):
        locs = set(rg.locs_around(loc, filter_out=('invalid', 'obstacle', 'spawn')))
        locs = locs - self.blocked_move_locs
        if len(locs) == 0:
            locs = set(rg.locs_around(loc, filter_out=('invalid', 'obstacle')))
            locs = locs - self.blocked_move_locs
        return list(locs)
    
    def getDamageTaken(self, my_bot):
        if len(self.my_bots_history) < 1:
            return 0
        else:
            for old_loc, old_bot in self.my_bots_history[len(self.my_bots_history)-1].iteritems():
                if old_bot.robot_id == my_bot.robot_id:
                    return old_bot.hp - my_bot.hp
            return 0
        
    # Returns a list of enemies near given loc with a walking dist of wdist
    def getNearbyEnemies(self, loc, wdist):
        nearbyEnemies = {}
        for enemy_loc, enemy_bot in self.enemy_bots.iteritems():
            if rg.wdist(loc, enemy_loc) <= wdist:
                nearbyEnemies[enemy_loc] = enemy_bot
        return nearbyEnemies
        
    def getNearbyFriendlies(self, loc, wdist):
        nearbyFriendlies = {}
        for my_loc, my_bot in self.my_bots.iteritems():
            if rg.wdist(loc, my_loc) <= wdist:
                nearbyFriendlies[my_loc] = my_bot
        return nearbyFriendlies
    
    def guard(self, my_bot):
        return ['guard']
    
    def attack(self, my_bot, loc):
        return ['attack', loc]
    
    def move(self, my_bot, loc):
        self.blocked_move_locs.remove(my_bot.location)
        self.blocked_move_locs.add(loc)
        return ['move', loc]
        
    def suicide(self, my_bot):
        self.blocked_move_locs.remove(my_bot.location)
        return['suicide']
