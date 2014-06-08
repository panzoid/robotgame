import rg
import time
import random

# version 0.2.3

class Robot:
    def __init__(self):
        self.turn = -1
        self.firstActTimeLimitMilli = 1500
        self.subsequentActTimeLimitMilli = 300
        self.my_bots_history = []
        self.enemy_bots_history = []
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
        # List of locations where my bots are planning to move
        self.planned_move_locs = []
        
        for loc, bot in self.game.robots.iteritems():
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
        # Surround the enemy, if the bot is already next to the enemy then decide to attack or guard or suicide if the bot is surrounded.
        shortest = None
        
        #if my_bot.hp <= rg.settings.attack_range[1]:
        #    return self.panic(my_bot)
        
        for enemy_loc, enemy_bot in self.enemy_bots.iteritems():
            dist = rg.dist(my_bot.location, enemy_loc)
                
            # Found enemy adjacent to bot, attack it or guard
            if dist <= 1:
                return self.guardOrAttack(my_bot, enemy_bot)
            # Found enemy two spaces away, attack open spot in between in case it moves there.
            #elif dist <= 2 and random.randint(0,1) == 1:
            #    return self.preemptiveAttack(my_bot, enemy_bot)
            # Find the enemy closest to bot, ignoring any enemies that are already surrounded
            if len(self.open_locs_around(enemy_loc)) > 0:
                if shortest == None or dist < shortest[0]:
                    shortest = (dist, enemy_loc)
                    
        # Bot is not directly next to enemy, try to move to a spot adjacent to the closest enemy. 
        if shortest != None:     
            return self.moveTowards(my_bot, shortest[1])
        # All enemy bots are surrounded, just default this bot to move towards center or guard if already at center.
        else:
            return self.moveTowards(my_bot, rg.CENTER_POINT)
    
    def guardOrAttack(self, my_bot, enemy_bot):
        self.planned_move_locs.append(my_bot.location)
        if self.getDamageTaken(my_bot) > 10:
            return ['guard']
        else:
            return['attack', enemy_bot.location]
            
    def preemptiveAttack(self, my_bot, enemy_bot):
        return['attack', rg.toward(my_bot.location, enemy_bot.location)]
    
    # Moves the bot towards the loc, going around any obstacles. If bot is already at loc then just guard.
    def moveTowards(self, my_bot, loc):
        if my_bot.location == loc:
            self.planned_move_locs.append(my_bot.location)
            return ['guard']
        
        locs = self.open_locs_around(my_bot.location)
        # bot has nowhere to move include spawn points
        if len(locs) == 0:
            locs = self.open_locs_around(my_bot.location, spawn=False)
            # if bot still has nowhere to move then just guard
            if len(locs) == 0:
                self.planned_move_locs.append(my_bot.location)
                return ['guard']
        
        locs = sorted(locs, key=lambda x: rg.dist(x, loc))
        
        self.planned_move_locs.append(locs[0])
        return ['move', locs[0]]
    
    # Returns open locations sorted by distance that are adjacent to destination location
    def open_locs_around(self, loc, spawn=True):
        locs = []
        if spawn:
            locs = rg.locs_around(loc, filter_out=('invalid', 'obstacle', 'spawn'))
        else:
            locs = rg.locs_around(loc, filter_out=('invalid', 'obstacle'))
        for i in locs:
            if i in self.enemy_bots or i in self.planned_move_locs:
                locs.remove(i)
        return locs
    
    def getDamageTaken(self, my_bot):
        if len(self.my_bots_history) < 1:
            return 0
        else:
            for old_loc, old_bot in self.my_bots_history[len(self.my_bots_history)-1].iteritems():
                if old_bot.robot_id == my_bot.robot_id:
                    return old_bot.hp - my_bot.hp
            return 0
