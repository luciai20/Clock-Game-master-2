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

        for constraint in constraints: 
            match constraint.count('<'): 
                case 1: keep = self.__keep2LetterConstraint(cards, constraint)
                case 2: keep = self.__keep3LetterConstraint(cards, constraint)
                case 3: keep = self.__keep4LetterConstraint(cards, constraint)
                case 4: keep = self.__keep5LetterConstraint(cards, constraint)
            if keep: final_constraints.append(constraint)
                    
        return final_constraints



    #def play(self, cards: list[str], constraints: list[str], state: list[str], territory: list[int]) -> Tuple[int, str]:
    def play(self, cards, constraints, state, territory):
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
        #Do we want intermediate scores also available? Confirm pls
        
        letter = self.rng.choice(cards)
        territory_array = np.array(territory)
        available_hours = np.where(territory_array == 4)
        hour = self.rng.choice(available_hours[0])          #because np.where returns a tuple containing the array, not the array itself
        hour = hour%12 if hour%12!=0 else 12
        return hour, letter
    
    def __keep2LetterConstraint(self, cards, constraint): 
        return constraint[0] in cards or constraint[2] in cards
    
    def __keep3LetterConstraint(self, cards, constraint): 
        counter = 0
        for letter in constraint: 
            if letter in cards: counter += 1
            if counter == 2: return True 
        return False 
    
    def __keep4LetterConstraint(self, cards, constraint): 
        if constraint[0] in cards and constraint[4] in cards: return True 
        elif constraint[2] in cards and (constraint[4] or constraint[6]) in cards: return True 
        elif self.__howManyLetters(cards, constraint) in [3,4]: return True 
        return False 
    
    def __keep5LetterConstraint(self, cards, constraint): 
        counter = 0 
        for letter in constraint: 
            if letter in cards: counter += 1 
            if counter == 2: return True 
        return False 
    
    def __howManyLetters(self, cards, constraint): 
        counter = 0 
        for letter in constraint: 
            if letter in cards: counter += 1
        return counter

