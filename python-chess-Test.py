"""
Docs: https://pypi.python.org/pypi/python-chess
"""
import chess
import chess.uci

b = chess.Board()
e = chess.uci.popen_engine("/home/luckcow/coding/chessAI/cow-chess.py")
print(e.process)
print(e.author)
print("engine open")
e.uci()
print(e.is_alive())
e.isready()
print("Author: ", e.author)
e.position(b)
command = e.go()
b.push(command.bestmove)
print(b)

'''
board = chess.Board()
board.push_san("e4")
print(board.legal_moves)
print(board)
'''