#!/usr/bin/python3
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


message = input("> ")
print(emoji_converter(message))
