# -*- coding: utf-8 -*-
import sys, lark

'''--- Globals ---'''
import sys
g_dbg = ('-dbg' in sys.argv) or False

def parser():
  out = lark.Lark(r"""
    term: variable
       | application
       | abstraction
    application: "(" term term ")"
    abstraction: "[" var "." term "]"
        | "[" lambda var "." term "]"
    lambda: "\\" | "L" | "l" | "\\L" | "\\l"
    variable: LETTER
    %import common.LETTER
    %import common.WS
    %ignore WS
    """, start = "term")
  return out

'''--- Main ---'''
def main():
  print parser().parse(sys.argv[1]).pretty()
if __name__ == '__main__':
    main()