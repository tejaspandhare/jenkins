#!/usr/bin/python3
import sys

def emoji_converter(message):
    split_message = message.split(" ")
    emojis_set = {
        ":)" : "🙂",
        ":(" : "😔"
    }
    output = " "
    for i in split_message:
        output += emojis_set.get(i, i) + " "
    return output

# Read message from standard input
message = sys.stdin.readline().strip:()
print(emoji_converter(message))
