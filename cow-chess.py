#!/usr/bin/python3
"""
Engine: Cow Chess
Author: Nick Collins
7/21/2016

UCI Protocol
http://wbec-ridderkerk.nl/html/UCIProtocol.html

Possible additions:
Negamax
Iterative Deepening
Quiescence Search: continue searching interesting positions until they quiet down to avoid horizon effect
Hash tables: Hash position(Zobrist) store move, score, and depth searched
Forward Move Pruning:
--Null Move Pruning: before moving, do a reduced depth search with opponent to move with same position
----Do not need to search subtree if opponent cannot do anything to you
----(Fails in zugzwang)
--Late Move Reductions (not sure what this is)?
--Futility pruning add margin of error at node before leaf nodes to see if it raises best value
----If even 3 points can't raise the value, it does not need to be searched
"""

import sys
import chess
import random

class AI:
    def __init__(self):
        self.board = chess.Board()
        self.depthLimit = 2

    def set_position(self, posStr):
        if posStr.split()[0] == "startpos":
            self.board = chess.Board()
            if len(posStr.split()) > 2:
                for move in posStr.split(' ', 2)[2].split():
                    self.board.push_uci(move)
        elif posStr.split()[0] == "fen":
            fen, partition, moves = posStr.partition(" moves ")
            self.board = chess.Board(fen.split(' ', 1)[1])
            for move in moves:
                self.board.push_uci(move)
        #print(self.board)

    def new_game(self):
        self.board = chess.Board()
        
    def make_move(self):
        #TODO: MINIMAX
        #TODO: Alpha-Beta Pruning
        #TODO: Opening Book
        #print("bestmove e2e4")

        '''
        moves = list(self.board.legal_moves)
        move = str(random.choice(moves))
        sys.stdout.write("Confusing message for debugging?"+'\n')
        sys.stdout.flush()
        '''
        move, score = self.minimax(None, -1, -101, 101)
        print("Best score: {}".format(score))
        sys.stdout.write("bestmove " + move + '\n')
        sys.stdout.flush()

    def minimax(self, move, depth, alpha, beta):
        depth += 1
        if depth > 0:
            self.board.push_uci(move)
            
        if self.board.is_game_over():
            # Draws
            # Seventyfive-move rule.
            if self.board.halfmove_clock >= 150:
                score = 0.0
            # Insufficient material.
            if self.board.is_insufficient_material():
                score =  0.0
            # Stalemate.
            if self.board.is_stalemate():
                score = 0.0
            # Fivefold repetition.
            if self.board.is_fivefold_repetition():
                score = 0.0

            # Checkmate. 
            if self.board.is_checkmate():
                if self.board.turn == chess.WHITE:
                    score = -100.0
                else:
                    score = 100.0
            if depth > 0:
                self.board.pop()
            return move, score

        elif depth == self.depthLimit:
            sc = self.board_score()
            self.board.pop()
            return move, sc
        else:
            if self.board.turn:
                bestScore = -101
                bestMove = None
                for m in (str(m) for m in self.board.legal_moves):
                    _, score = self.minimax(m, depth, alpha, beta)
                    if score > bestScore:
                        bestScore = score
                        bestMove = m
                    alpha = max(alpha, bestScore)
                    if beta <= alpha:
                        break
            else:
                bestScore = 101
                bestMove = None
                for m in (str(m) for m in self.board.legal_moves):
                    _, score = self.minimax(m, depth, alpha, beta)
                    if score < bestScore:
                        bestScore = score
                        bestMove = m
                    beta = min(beta, bestScore)
                    if beta <= alpha:
                        break

            if depth > 0:
                self.board.pop()
            return bestMove, bestScore


    def board_score(self):
        '''
        Evaluate the current board
        Using weighted linear combination of features on the chess board

        Note: values are absolute: must be cahnged relative to player for negamax framework
        '''
        PIECE_VALUES = [1, 3, 3, 5, 9, 100]
        score = 0
        materialScore = 0
        for t in chess.PIECE_TYPES:
            materialScore += PIECE_VALUES[t-1] * len(self.board.pieces(t, chess.WHITE))
            materialScore -= PIECE_VALUES[t-1] * len(self.board.pieces(t, chess.BLACK))
        #TODO: Pawn structure
        #TODO: Bishop pair
        #TODO: King safety
        #TODO: Offense
        #TODO: Piece Square table (Knights and pawns in center, rooks on open files)
        #TODO: Defense
        #TODO: options (Mobility)
        #TODO: Tapered evaluation: different evaluation function for different times in game
        #TODO: Endgame tables
        #print("Board scored: {}".format(materialScore))
        return materialScore


if __name__ == "__main__":
    ai = AI()
    while(1):
        inStr = sys.stdin.readline()
        command = None
        if inStr:
            command = inStr.split()[0]
        
        if command == "uci":
            sys.stdout.write("id name Cow Chess"+'\n')
            sys.stdout.flush()
            sys.stdout.write("id author Nick Collins!"+'\n')
            sys.stdout.flush()
            #Send changable options
            #print("option name NAME type TYPE default")
            #setup initial parameters
            
            sys.stdout.write("uciok"+'\n')
            sys.stdout.flush()
            
        elif command == "isready":
            #Finish initializing
            sys.stdout.write("readyok"+'\n')
            sys.stdout.flush()
            #print("readyok")
            
        elif command == "setoption": #TODO: set options
            pass

        elif command == "ucinewgame":
            ai.new_game()
            
        elif command == "position":
            ai.set_position(inStr.split(' ', 1)[1])
        
        elif command == "go":
            ai.make_move()