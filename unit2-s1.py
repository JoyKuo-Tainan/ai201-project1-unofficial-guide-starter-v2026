# student = {"name": "Alice", "age": 20, "grade": "A"}

# # insert
# student["emial"] = "alice@xyz.com"
# student.update({"major": "CS", "year": 4})

# read
# print(student["email"])
# print(student.get("phone"))
# print(student.get("phone", "N/A"))

# check for existence
# print("email" in student.values())
# print("address" in student)

# # iterate
# for key in student:
#     print(key)

# for value in student.values():
#     print(value)

# for key, value in student.items():
#     print(key, value)

# # update
# student["grade"] = "B"
# # you cannot change the keys.


# def word_count(words):
#     if len(words) == 0:
#         return {}
#     counts = {}
#     for word in words:
#         if word in counts:
#             counts[word] += 1
#         else:
#             counts[word] = 1
#     return counts

artists1 = ["Kendrick Lamar", "Chappell Roan", "Mitski", "Rosalia"]
set_times1 = ["9:30 PM", "5:00 PM", "2:00 PM", "7:30 PM"]

# def lineup(artists, set_times):
#     if len(artists) == 0 or len(set_times) == 0:
#         return {}

#     time = {}
#     for i in range(len(artists)):
#         time.update({artists[i]: set_times[i]})

#     return time

# print(lineup(artists1, set_times1))

# def get_artist_info(artist, festival_schedule):

#     if len(artist) == 0 or len(festival_schedule) == 0:
#         return {"message": "Artist not found"}
    
#     return festival_schedule.get(artist, {"message": "Artist not found"})

# festival_schedule = {
#     "Blood Orange": {"day": "Friday", "time": "9:00 PM", "stage": "Main Stage"},
#     "Metallica": {"day": "Saturday", "time": "8:00 PM", "stage": "Main Stage"},
#     "Kali Uchis": {"day": "Sunday", "time": "7:00 PM", "stage": "Second Stage"},
#     "Lawrence": {"day": "Friday", "time": "6:00 PM", "stage": "Main Stage"}
# }

# print(get_artist_info("Blood Orange", festival_schedule)) 
# print(get_artist_info("Taylor Swift", festival_schedule))  

def identify_conflicts(venue1_schedule, venue2_schedule):
    if len(venue1_schedule)==0 or len(venue2_schedule)==0:
        return {}
    conflicts = {}
    for k, v in venue1_schedule.items():
        if k in venue2_schedule:
            if v == venue2_schedule.get(k):
                conflicts[k] = v
    return conflicts

venue1_schedule = {
    "Stromae": "9:00 PM",
    "Janelle Monáe": "8:00 PM",
    "HARDY": "7:00 PM",
    "Bruce Springsteen": "6:00 PM"
}

venue2_schedule = {
    "Stromae": "9:00 PM",
    "Janelle Monáe": "10:30 PM",
    "HARDY": "7:00 PM",
    "Wizkid": "6:00 PM"
}

print(identify_conflicts(venue1_schedule, venue2_schedule))
