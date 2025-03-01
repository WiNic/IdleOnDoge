from enum import IntEnum

from pydantic import BaseModel, field_validator


class RankUpGpRequirement(IntEnum):
    COPPER= 1_000
    SILVER= 2_000
    GOLD= 5_000
    PLAT= 10_000 
    LUSTRE= 15_000
    DREADLO= 25_000
    VOID= 50_000

#PRODUCTION
RANK_ROLE_IDS = {
    "COPPER": 1092613585999507596,
    "SILVER": 1092614562295070750,
    "GOLD":   1092618166359822446,
    "PLAT":   1114564626240254082,
    "LUSTRE": 1142466976732692631,
    "DREADLO":1191079636701040672,
    "VOID":   1278847206224302263
}
#test
# RANK_ROLE_IDS = {
#     "COPPER": 1345230184391114824, #this
#     "LUSTRE": 1345230086835671040, #this

# }

def determine_rank(gp_value: int) -> str:
    """
    Given a GP value, returns the name of the rank that is reached.
    If the gp_value is less than the lowest threshold, returns None.
    """
    last_rank = None
    for rank in RankUpGpRequirement:
        if gp_value >= rank:
            last_rank = rank
        else:
            break
    return last_rank.name if last_rank is not None else None

class UserInput(BaseModel):
    """
    Pydantic model to validate:
      - year: an integer in [2024..2100]
      - month: an integer in [1..12]
      - n: an integer in [1..20]
    """
    year: int
    month: int
    n: int

    @field_validator('year')
    @classmethod
    def check_year(cls, value):
        if not (2024 < value < 2100):
            raise ValueError("Year must be between 2024 and 2099!")
        return value

    @field_validator('month')
    @classmethod
    def check_month(cls, value):
        if not (1 <= value <= 12):
            raise ValueError("Month must be between 1 and 12!")
        return value
    
    @field_validator('n')
    @classmethod
    def check_n(cls, value):
        if not (1 <= value <= 20):
            raise ValueError("number of top members needs to be between 1 and 20!")
        return value

def validate_input(year: int, month: int, n: int) -> UserInput:
    """
    Validates year, month, and n using Pydantic.
    Returns a UserInput object if valid; raises ValidationError if not.
    """
    return UserInput(year=year, month=month, n=n)

def generate_leaderboard(entries: list[tuple[str, int]]) -> list[tuple[int, str, int]]:
    """
    Generates a leaderboard from a list of (name, score) tuples.
    If multiple entries have the same score, they share the same rank.
    
    Parameters:
        entries (list[tuple[str, int]]): List of (name, score) tuples.
    
    Returns:
        list[tuple[int, str, int]]: A list of (rank, name, score) tuples.
    """
    # Sort entries by score (descending) and name (ascending as a tie-breaker)
    
    leaderboard = []
    prev_score = None
    rank = 0
    count = 0  # Total entries processed
    
    for name, score in entries:
        count += 1
        # Update rank if score changes from previous entry
        if score != prev_score:
            rank = count
        leaderboard.append((rank, name, score))
        prev_score = score
    
    return leaderboard
