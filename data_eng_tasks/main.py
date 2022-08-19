"""
Human Digital - Data Engineering Interview Task
Author: Eduardo dos Santos
Date: 19/8/2022 10:50
"""

import json
import os
from datetime import datetime as dt
from pprint import pprint as pp

VIDEOS_FILENAME = "videos.json"
COMMENTS_FILENAME = "comments.json"

STATS_CSV_FILENAME = "stats.csv"

PUBLISHEDTIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

videos_list = None
comments_list = None

def load_datafiles():
    """
    Loads videos and comments datasets from their respective JSON files..
    Stores videos in `videos_list` and comments in `comments_list` global variables.
    :return:
    """
    global videos_list, comments_list
    videos_list = json.load(open(VIDEOS_FILENAME, encoding="utf-8"))
    #print("=========VIDEOS==========")
    #pp(videos_list)
    #print("=========COMMENTS==========")
    comments_list = json.load(open(COMMENTS_FILENAME, encoding="utf-8"))
    #pp(comments_list)

def get_total_videos_and_comments():
    """
    - The number of unique videos and the number of comments printed to command line.
    :return:
    """
    global videos_list, comments_list

    total_videos = sum([len(videos_list[i]["items"]) for i in range(len(videos_list))])

    # Each comment may be formed by the comment itself and associated replies. Each comment may have 0 or more replies.
    # Here, comment replies are treated like comments.

    # If a comment has no replies, it will count as 1 comment (itself). However, if there are replies, it will count as the number of replies plus 1 (itself).
    total_comments = sum([1 if c["replies"] is None else len(c["replies"]) + 1 for c in comments_list])

    print("Total number of videos: {tv}. Total number of comments: {tc}".format(
        tv=total_videos, tc=total_comments))


def get_total_comments_for_video():
    """
    - A human-readable print to command line, detailing  the number of comments associated with each video

    :return:
    """
    # First retrieves all `videoId`s.
    video_ids = [videos_list[i]["items"][j]["id"] for i in range(len(videos_list)) for j in
                 range(len(videos_list[i]["items"]))]

    # creates a dictionary to store the number of comments (value) associated with each videoId (key)
    comments_dict = {v: 0 for v in video_ids}
    # processes all comments, updating the number of comments for each videoId
    # videoIds might be at whatever order in the comments dataset
    for comment in comments_list:
        curr_videoid = comment["snippet"]["videoId"]
        comments_dict[curr_videoid] = comments_dict[curr_videoid] + (1 if comment["replies"] is None else len(comment["replies"]) + 1)

    print("Total of comments per video")
    for n, v in enumerate(comments_dict.keys()):
        print("\tVideo {} ({}): {} comments".format(n + 1, v, comments_dict[v]))


user_comments = {}
def update_user_comments_stats(author):
    """
    Accessory method for `get_user_comments()`.
    :param author:
    :return:
    """
    global user_comments

    if author in user_comments.keys():
        user_comments[author] = user_comments[author] + 1
    else:
        user_comments[author] = 1

def get_user_comments():
    """
    - A list of unique user display names who have commented on either video, and a count of the comments they posted, written to a CSV file

    :return:
    """
    # parses the comments dataset for authors
    # Like previous methods, replies to comments are treated like top-level comments.
    for comment in comments_list:
        author = comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
        update_user_comments_stats(author)

        # if there are replies associated with a particular comment, process these like comments
        has_replies = isinstance(comment["replies"], list) and len(comment["replies"]) > 0
        if has_replies:
            for reply in comment["replies"]["comments"]:
                reply_author = reply["snippet"]["authorDisplayName"]
                update_user_comments_stats(reply_author)

    #pp(user_comments)
    #print(sum(v for v in user_comments.values()))

    # creates a context to save comment data into a CSV file
    with open(STATS_CSV_FILENAME, "w+") as f:
        # TODO add exists check
        f.write("\'authorDisplayName\',\'msg_count\'")
        f.write("\n")
        for k, v in user_comments.items():
            k = replace_chars(str(k))
            f.write("\'")
            f.write(str(k))
            f.write("\','")
            f.write(str(v))
            f.write("'\n")

    print(f"Saving CSV file '{STATS_CSV_FILENAME}' with user stats.")

def replace_chars(k:str):
    """
    Accessory method. Replaces certain characters for better CSV compatibility.
    :param k:
    :return:
    """
    return k.replace(",","\\,")

def parse_date(date_str):
    """
    Accessory method. Parses a string into a Python `datetime` object.
    The default datetime format is defined in the `PUBLISHEDTIME_FORMAT` variable.
    :param date_str:
    :return:
    """
    return dt.strptime(date_str, PUBLISHEDTIME_FORMAT)

def get_time_first_comment():
    """
     - The time interval, in hours, minutes, and seconds, between the time each video was posted and the first comment was made on that video, printed to command line

    :return:
    """
    # stores `videoId` and associated `publishedAt` datetime for each video into a dictionary.
    videos_publishedAt_dict = {videos_list[i]["items"][j]["id"] : parse_date(videos_list[i]["items"][j]["snippet"]["publishedAt"]) for i in range(len(videos_list)) for j in
                 range(len(videos_list[i]["items"]))}

    # stores the time interval of the soonest comment for each videoId
    videos_first_comment_dict = {}

    #print(videos_publishedAt_dict)
    # processes the comments dataset.

    for comment in comments_list:
        # retrieves videoId associated with the comment
        comment_videoid = comment["snippet"]["topLevelComment"]["snippet"]["videoId"]
        # retrieves the time the comment was published
        # comment replies are not relevant here: we assume it is impossible for a reply to come before the `topLevelComment`
        # therefore we only deal with the `topLevelComment`
        comment_publishedAt = parse_date(comment["snippet"]["topLevelComment"]["snippet"]["publishedAt"])

        # check whether the videoId hasn't yet been processed at least once
        if comment_videoid not in videos_first_comment_dict:
            # stored the difference (timedelta obj) between the comment's publishedAt and the video's publishedAt

            videos_first_comment_dict[comment_videoid] = (comment_publishedAt - videos_publishedAt_dict[comment_videoid])
        # if there's already been a comment processed for the videoId,

        else:
            # retrieves the previously stored time interval for the same videoId
            stored_timeinterval = videos_first_comment_dict[comment_videoid]
            # timeinterval between current comment's published time and video's published time
            curr_comment_timeinterval = (comment_publishedAt - videos_publishedAt_dict[comment_videoid])

            # if the previously stored time interval is higher than the current time interval
            # this means the current comment came first; thus the quickest comment record is updated
            if stored_timeinterval > curr_comment_timeinterval:
                videos_first_comment_dict[comment_videoid] = curr_comment_timeinterval

    #pp(videos_first_comment_dict)

    print("Time interval between publication of video and first comment")
    for i, kv in enumerate(videos_first_comment_dict.items()):
        k = kv[0]
        v = kv[1]

        print(f"\tVideo {i} ({k}): {v}")


if __name__ == "__main__":
    load_datafiles()

    get_total_videos_and_comments()
    get_total_comments_for_video()
    get_user_comments()
    get_time_first_comment()


