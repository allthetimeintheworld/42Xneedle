def reverse_string(s):
    return s[::-1]

if __name__ == '__main__':
    import sys
    print(reverse_string(sys.argv[1]))