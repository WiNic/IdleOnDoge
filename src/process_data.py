# laod data from 

import json
from dataclasses import dataclass

from config import Config

config = Config()

def load_data(file_name:str)->dict:
    with open(config.data_folder / f"{file_name}.json") as file:
        data = json.load(file)
    return data

def get_newest_filename()->str:
    file_list = list(config.data_folder.glob("*.json"))
    file_list.sort()
    return file_list[-1].stem

def get_len_all_file_names_from_year_month(year:int, month:int)->int:
    all_files = list(config.data_folder.glob(f"*{year}-{month:02}*.json"))
    return len(all_files)


def get_newest_file_name_from_year_month(year:int, month:int)->str:
    all_files = list(config.data_folder.glob(f"*{year}-{month:02}*.json"))
    return all_files[0].stem

def get_oldest_file_name_from_year_month(year:int, month:int)->str:
    all_files = list(config.data_folder.glob(f"*{year}-{month:02}*.json"))
    return all_files[-1].stem



# check if file exists
def check_file_exist(file_name:str)->bool:
    return (config.data_folder / f"{file_name}.json").exists()




# Note ubnused for now
@dataclass
class LargeGuildMemberData:
    username: str  # Previously "a"
    b: str 
    c: int  
    level: int  # Previously "d"
    gp: int  # Previously "e"
    f: int  
    g: int  

@dataclass
class OnlyGPMember:
    username: str
    gp: int

GUILD_POINTS = 1


def guild_data_from_month(file_name:str)->dict:
    data = load_data(file_name)
    guild_data = data.get("guildData")
    if guild_data is None:
        members = data.get("members")
        guild_data = data
        if members is None: 
            raise ValueError("No guild data and no members found in file")
    return guild_data

def map_data(data:dict)->dict[str, OnlyGPMember]:
    members = {}
    guild_members:list[dict[str,int]] = data.get("members")
    #check if guild_members has "a" key or "name"

    for raw_data in guild_members:

        member = OnlyGPMember(
            username=raw_data.get("a") or raw_data.get("name"),
            gp=raw_data.get("e") or raw_data.get("gpEarned"),
        )

        if member.username is None:
            raise ValueError("No username found in member data")
        members[member.username] = member

    return members


def evaluate_monthly_gain(year:int, month:int, n:int)->list[tuple[str, int]]:
    files = get_len_all_file_names_from_year_month(year, month)
    if files < 2:
        raise ValueError(f"Not enough data to compare, currently only {files} files found for year {year} and month {month}")

    month_start = get_newest_file_name_from_year_month(year, month)
    guild_data_month_start = guild_data_from_month(month_start)
    members_month_start = map_data(guild_data_month_start)

    month_end = get_oldest_file_name_from_year_month(year, month)
    guild_data_month_end = guild_data_from_month(month_end)
    members_month_end = map_data(guild_data_month_end)


    diff_gp = get_diff_gp(members_month_start, members_month_end)
    
    sorted_members = sorted(diff_gp.items(), key=lambda x: x[1], reverse=True)

    if n >= len(sorted_members):
        n = len(sorted_members)-1
        print(n)

    while sorted_members[n-1][GUILD_POINTS] == sorted_members[n][GUILD_POINTS] and n < len(sorted_members):
        n += 1

    return sorted_members[:n]

# function to get diff of gp 
def get_diff_gp(members_month_start:dict[str, OnlyGPMember], members_month_end:dict[str, OnlyGPMember])->dict[str, int]:
    diff:dict[str, int] = {}
    for member in members_month_start.keys():
        try:
            diff_int = members_month_end.get(member).gp - members_month_start.get(member).gp
        except AttributeError:
            print(f"{member} not found in members_month_end")

        diff[member] = diff_int

    return diff


if __name__ == "__main__":
    monthly_gain = evaluate_monthly_gain(2025, 2, 175)
    print(monthly_gain)
    print(len(monthly_gain))
