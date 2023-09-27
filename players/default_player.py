from tokenize import String
import numpy as np
from typing import Tuple, List

class Player:
    def __init__(self, rng: np.random.Generator) -> None:
        """Initialise the player with given skill.

        Args:
            skill (int): skill of your player
            rng (np.random.Generator): numpy random number generator, use this for same player behvior across run
            logger (logging.Logger): logger use this like logger.info("message")
            golf_map (sympy.Polygon): Golf Map polygon
            start (sympy.geometry.Point2D): Start location
            target (sympy.geometry.Point2D): Target location
            map_path (str): File path to map
            precomp_dir (str): Directory path to store/load precomputation
        """
        self.discardPile = []
        self.queue = []
        self.rng = rng

    #def choose_discard(self, cards: list[str], constraints: list[str]):
    def choose_discard(self, cards, constraints):
        """Function in which we choose which cards to discard, and it also inititalises the cards dealt to the player at the game beginning

        Args:
            cards(list): A list of letters you have been given at the beginning of the game.
            constraints(list(str)): The total constraints assigned to the given player in the format ["A<B<V","S<D","F<G<A"].

        Returns:
            list[int]: Return the list of constraint cards that you wish to keep. (can look at the default player logic to understand.)
        """
        final_constraints = []
        twoLetterConstraints = []
        threeLetterConstraints = []
        fourLetterConstraints = []
        fiveLetterConstraints = []

        #only parse first 100 constraints to avoid crashing with time complexity 
        if len(constraints) > 100:
            constraints = constraints[:100]
        
        #separate constraints by size 
        for constraint in constraints: 
            if not self.__checkPairs(cards, constraint): continue 
            if len(constraint) == 3: 
                twoLetterConstraints.append(constraint)
            elif len(constraint) == 5: 
                threeLetterConstraints.append(constraint)
            elif len(constraint) == 7: 
                fourLetterConstraints.append(constraint)
            else: 
                fiveLetterConstraints.append(constraint)

        if len(twoLetterConstraints) > 10: 
            twoLetterConstraints = self.__chooseTwoLetterConstraints(twoLetterConstraints, threeLetterConstraints, fourLetterConstraints, fiveLetterConstraints, cards)
        if len(threeLetterConstraints) > 5: 
            threeLetterConstraints = self.__chooseThreeLetterConstraints(twoLetterConstraints, threeLetterConstraints, cards)
        if len(fourLetterConstraints) > 3: 
            fourLetterConstraints = self.__chooseFourLetterConstraints(twoLetterConstraints, fourLetterConstraints)
        if len(fiveLetterConstraints) > 2: 
            fiveLetterConstraints = self.__chooseFiveLetterConstraints(twoLetterConstraints, fiveLetterConstraints, cards)
        final_constraints = twoLetterConstraints + threeLetterConstraints + fourLetterConstraints + fiveLetterConstraints

        self.__getDiscard(cards, final_constraints)
        return final_constraints



    #def play(self, cards: list[str], constraints: list[str], state: list[str], territory: list[int]) -> Tuple[int, str]:
    def play(self, cards, constraints, state, territory):
        print("\n cards: ", cards)
        """Function which based n current game state returns the distance and angle, the shot must be played

        Args:
            score (int): Your total score including current turn
            cards (list): A list of letters you have been given at the beginning of the game
            state (list(list)): The current letters at every hour of the 24 hour clock
            territory (list(int)): The current occupiers of every slot in the 24 hour clock. 1,2,3 for players 1,2 and 3. 4 if position unoccupied.
            constraints(list(str)): The constraints assigned to the given player

        Returns:
            Tuple[int, str]: Return a tuple of slot from 1-12 and letter to be played at that slot
        """
        letter = None  #because np.where returns a tuple containing the array, not the array itself
        hour = None          
        territory_array = np.array(territory)
        available_hours = np.where(territory_array == 4)
        #parse all constraints from smallest to biggest

        constraints.sort()
        for constraint0 in constraints: 
            print("larger constraint: ", constraint0)
            #if we have a good play with letter AND hour, stop checking constraints 
            if (letter is not None or self.queue != []) and hour is not None:  
                print("already have good play")
                break
            #if we have all letters, queue them
            if self.__readyToPlay(cards, state, constraint0): 
                print("have all letters in larger constraint") 
                self.__queueAllLetters(cards, constraint0)
            else: 
                #if constraint is not ready to be played, continue (play from queue or discard)
                continue
            #split constraint into smaller 2 letter constraints 
            #ex. U<O<C will become ["U<O", "O<C"]
            for constraint in self.__getSmallerConstraints(constraint0):
                print("smaller constraint: ", constraint)
                #2 letter constraint where we have 1 letter, check that other letter was played 
                playedAt = self.__wasPlayedAt(constraint[2], state)
                if constraint[0] in cards and playedAt is not None: 
                    print(constraint[0], " in cards and ", constraint[2], " was played at ", playedAt)
                    hour = self.__chooseHour(playedAt, state, False)
                    break
                playedAt = self.__wasPlayedAt(constraint[0], state)
                if constraint[2] in cards and playedAt is not None: 
                    print(constraint[2], " in cards and ", constraint[0], " was played at ", playedAt)
                    hour = self.__chooseHour(playedAt, state, True)
                    break 

        #if only 1 card left and we don't have good play just play randomly
        if len(cards) == 1: 
            return self.__chooseRandomHour(state, available_hours), cards[0]
                    
        #play next in queue if not empty
        if letter is None and self.queue != []: 
            letter = self.queue.pop(0)
            print("playing from queue: ", letter)
        #play from discard if not empty 
        elif letter is None: 
            if self.discardPile != []:
                print("playing from discard")
                letter = self.rng.choice(self.discardPile)
                self.discardPile.remove(letter)
            else: 
                print("playing next best play")
                self.__chooseNextBestPlay(state, cards, constraints)
        
        #territory_array = np.array(territory)
        #available_hours = np.where(territory_array == 4)
        if hour is None:   
            hour = self.__chooseRandomHour(state, available_hours)
        print("returning: ", hour, letter)
        return hour, letter
    
    def __checkPairs(self, cards, constraint): 
    #treat constraint as collection of pairs and check each pair 
        i = 0
        while i < len(constraint)-1:  
            if not self.__havePair(cards, constraint[i], constraint[i+2]):
                return False
            i += 2
        return True

    def __havePair(self, cards, letter1, letter2): 
    #check if we have atleast 1 letter in pair of letters 
        return letter1 in cards or letter2 in cards
    
    #choose 10 best 2 letter constraints 
    def __chooseTwoLetterConstraints(self, twoLetterConstraints, threeLetterConstraints, fourLetterConstraints, fiveLetterConstraints, cards):
        finalConstraints = []
        leftover = []
        for constraint in twoLetterConstraints: 
            #prioritize constraints that are part of larger constraint 
            if self.__isInLargerConstraint(constraint, fiveLetterConstraints): 
                finalConstraints.insert(0, constraint)
            elif self.__isInLargerConstraint(constraint, fourLetterConstraints): 
                finalConstraints.insert(0, constraint)
            elif self.__isInLargerConstraint(constraint, threeLetterConstraints): 
                finalConstraints.insert(0, constraint)
            #next priority is we have both letters
            elif constraint[0] in cards and constraint[2] in cards:
                finalConstraints.append(constraint)
            else: 
                leftover.append(constraint)
        #only keep first 10 prioritized constraints
        if len(finalConstraints) > 10: return finalConstraints[:11]
        elif len(finalConstraints) == 10: return finalConstraints
        else: return finalConstraints + leftover[:(10-len(finalConstraints))]

    #choose 5 best 3 letter constraints 
    def __chooseThreeLetterConstraints(self, twoLetterConstraints, threeLetterConstraints, cards): 
        finalConstraints = []
        leftover = []
        for constraint in threeLetterConstraints: 
            #prioritize if it has a smaller constraint inside that we're keeping 
            if self.__hasSmallerConstraint(twoLetterConstraints, constraint): 
                finalConstraints.insert(0, constraint)
            #next prioritize if we have 2 letters
            elif self.__lettersMissing(cards, constraint) == 2: 
                finalConstraints.append(constraint)
            else: 
                leftover.append(constraint)
        if len(finalConstraints) > 5: return finalConstraints[:5]
        elif len(finalConstraints) == 5: return finalConstraints
        else: return finalConstraints + leftover[:5-(len(finalConstraints))]

    #choose 3 best 4 letter constraints 
    def __chooseFourLetterConstraints(self, twoLetterConstraints, fourLetterConstraints): 
        finalConstraints = []
        for constraint in fourLetterConstraints: 
            #prioritize if it has a smaller constraint inside that we're keeping 
            if self.__hasSmallerConstraint(twoLetterConstraints, constraint): 
                finalConstraints.insert(0, constraint)
            else: 
                finalConstraints.append(constraint)
        if len(finalConstraints) > 3: return finalConstraints[:3]
        else: return finalConstraints
    
    def __chooseFiveLetterConstraints(self, twoLetterConstraints, fiveLetterConstraints, cards): 
        finalConstraints = []
        leftover = []
        for constraint in fiveLetterConstraints: 
            #prioritize if it has a smaller constraint inside that we're keeping 
            if self.__hasSmallerConstraint(twoLetterConstraints, constraint): 
                finalConstraints.insert(0, constraint)
            #next prioritize if we have 3 letters 
            elif self.__lettersMissing(cards, constraint) == 2: 
                finalConstraints.append(constraint)
            else: leftover.append(constraint)
        if len(finalConstraints) > 2: return finalConstraints[:2]
        elif len(finalConstraints) == 2: return finalConstraints
        else: return finalConstraints + leftover[:(2-len(finalConstraints))]

    def __hasSmallerConstraint(self, smallerConstraints, largerConstraint): 
        largerConstraint = "".join(largerConstraint)
        for constraint in smallerConstraints: 
            if "".join(constraint) in largerConstraint:
                return True 
        return False
    
    def __isInLargerConstraint(self, smallerConstraint, largerConstraints): 
        smallerConstraint = "".join(smallerConstraint)
        for constraint in largerConstraints: 
            if smallerConstraint in "".join(constraint):
                return True 
        return False
    
    #create discard pile 
    def __getDiscard(self, cards, constraints):
        for card in cards: 
            if self.__isDiscard(card, constraints): 
                self.discardPile.append(card)

    #determine if we have all letters in a constraint
    def __isDiscard(self, card, constraints): 
        for constraint in constraints: 
            if card in constraint: return False 
        return True 

    #check if we have all letters in constraint
    def __lettersMissing(self, cards, constraint): 
        i = 0 
        lettersMissing = 0
        while i < len(constraint):  
            if constraint[i] not in cards: 
                lettersMissing += 1
            i+=2
        return lettersMissing
    
    #check if all letters in constraint are either in our cards our on the board 
    def __readyToPlay(self, cards, state, constraint): 
        i = 0 
        while i < len(constraint): 
            if constraint[i] not in cards and constraint[i] not in state:
                return False
            i += 2 
        return True 
    
    #queue all letters that we have 
    def __queueAllLetters(self, cards, constraint): 
        i = len(constraint) - 1
        while i >= 0: 
            if constraint[i] in cards and constraint[i] not in self.queue: 
                self.queue.insert(0, constraint[i])
            i -= 2 
    
    #check if letter was played
    def __wasPlayedAt(self, letter, state): 
        for hour, letterAtHour in enumerate(state): 
            if letter == letterAtHour: 
                return hour
        return None 
    
    #chooseHour that we want to play at when other letter in 2 letter constraint is played  
    def __chooseHour(self, hourPlayed, state, clockwise):
        if hourPlayed < 12: 
            hourPlayed = hourPlayed + 12 
        if clockwise:  
            i = 5
            while i > 0: 
                hour = (hourPlayed+i)%24
                if state[hour] == 'Z': return hour
                complimentary = self.__getComplimentary(hour)
                if state[complimentary] == 'Z': return complimentary
                i -= 1 
        else: 
            i = 5 
            while i > 0: 
                hour = (hourPlayed-i)%24
                if state[hour] == 'Z': return hour 
                complimentary = self.__getComplimentary(hour)
                if state[complimentary] == 'Z': return complimentary
                i -= 1

    def __chooseNextBestPlay(self, state, cards, constraints): 
        for constraint0 in constraints: 
            print("larger constraint: ", constraint0)
            for constraint in self.__getSmallerConstraints(constraint0): 
                print("smaller constraint: ", constraint)
                playedAt = self.__wasPlayedAt(constraint[0], state)
                if playedAt is not None and constraint[2] in cards: 
                    print(constraint[0], " was played at ", playedAt, " and ", constraint[2], " in cards")
                    hour = self.__chooseHour(playedAt, state, True)
                    letter = constraint[2]
                    print("returning: ", hour, letter)
                    return hour, letter
                playedAt = self.__wasPlayedAt(constraint[2], state)
                if playedAt is not None and constraint[0] in cards: 
                    print(constraint[2], " was played at ", playedAt, " and ", constraint[0], " in cards")
                    hour = self.__chooseHour(playedAt, state, False)
                    letter = constraint[2]
                    print("returning: ", hour, letter)
                    return hour, letter

    #for when we choose from discard or random 
    #instead of getting random hour we want to play at an hour that has both slots empty if possible 
    def __chooseRandomHour(self, state, availableHours): 
        i = 0 
        while i < 12: 
            if state[i] == 'Z' and state[i+12] == 'Z': return i 
            i += 1
        hour = self.rng.choice(availableHours[0])
        return hour%12 if hour%12!=0 else 12
        

    #if hour == 0, return 12 and viceversa
    def __getComplimentary(self, hour):
        if hour >= 12: 
            return hour%12
        else: 
            return hour+12
    
    #split larger constraints up into groups of 2 letter constraints 
    def __getSmallerConstraints(self, constraint): 
        i = 0 
        finalConstraints =  []
        while i < len(constraint)-1: 
            finalConstraints.append(constraint[i] + '<' + constraint[i+2])
            i += 2
        return finalConstraints

        



