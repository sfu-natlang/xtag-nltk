

def get_next_token(s,index,length = None):
    # state = 0: outside anything
    # state = 1: inside ""
    # state = 2: inside identifier
    # state = 3: inside comment (not for sure)
    state = 0
    start = 0
    end = 0
    # length is the length of s, just for speed up if the length can be
    # calculated outside of this function and doesn't change
    if length == None:
        l = len(s)
    else:
        l = length
        
    while True:
        if index >= l:
            if state == 0:
                return (None,index)
            else:
                return (s[start:l - 1],index)
        elif state == 0 and s[index].isspace():
            index += 1
        elif state == 0 and (s[index] == '(' or s[index] == ')' or s[index] == ':'):
            return (s[index],index + 1)
        elif state == 0 and s[index] == '"':
            start = index
            state = 1
            index += 1
        elif state == 1 and s[index] == '"':
            end = index
            state = 0
            return (s[start:end + 1],index + 1)
        elif state == 0 and (s[index].isalnum() or s[index] == "'"):
            state = 2
            start = index
            index += 1
        elif state == 2 and (s[index].isspace() or s[index] == ')' or s[index] == '('):
            end = index - 1
            return (s[start:end + 1],index)
        elif state == 0 and (s[index] == ';' or s[index] == '#'):
            state = 3
            index += 1
        elif state == 3 and s[index] == '\n':
            state = 0
            index += 1
        else:
            index += 1