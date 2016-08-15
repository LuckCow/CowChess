#!/usr/bin/python3
"""
Engine: Cow Chess
Author: Nick Collins
7/21/2016

Dependencies: python-chess 0.15.0 (pip)
Pychess (ubuntu repositories)

UCI Protocol
http://wbec-ridderkerk.nl/html/UCIProtocol.html

Possible additions:
Negamax
Iterative Deepening
Quiescence Search: continue searching interesting positions until they quiet down to avoid horizon effect
Hash tables: Hash position(Zobrist) store move, score, and depth searched
-- Each poistion hash is key to a list containing the move searched and the resulting score (and depth to make sure it is deep enough)
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

PIECE_VALUES = [1, 3, 3, 5, 9, 100]

class AI:
    def __init__(self):
        self.board = chess.Board()
        self.depthLimit = 4
        #self.positionCounter = {} #Tests number of positions in 1 iteration of minimax tree
        self.transposition_table = {}

    def set_position(self, posStr):
        if posStr.split()[0] == "startpos":
            self.board = chess.Board()
            if len(posStr.split()) > 2:
                for move in posStr.split(' ', 2)[2].split():
                    self.board.push_uci(move)
        elif posStr.split()[0] == "fen":
            fen, partition, moves = posStr.partition(" moves ")
            self.board = chess.Board(fen.split(' ', 1)[1])
            for move in moves.split():
                self.board.push_uci(move)
        #print(self.board)

    def new_game(self):
        self.board = chess.Board()
        
    def make_move(self):
        #TODO: Opening Book
        #TODO: Negamax

        self.transposition_table = {}
        move, score = self.minimax(None, -1, -101, 101)
        print("Best score: {}".format(score))
        sys.stdout.write("bestmove " + move + '\n')
        sys.stdout.flush()

    def minimax(self, move, depth, alpha, beta):
        depth += 1
        if depth > 0:
            self.board.push_uci(move)

            hash = self.board.incremental_zobrist_hash
            if hash in self.transposition_table:
                hmove, score, d = self.transposition_table[hash]
                if d >= depth:
                    self.board.pop()
                    return hmove, score
                
            
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
            bestScore = score

        elif depth == self.depthLimit:
            bestScore = self.board_score()
        else:
            if self.board.turn:
                bestScore = -101
                bestMove = None
                for m in (str(m) for m in self.board.legal_moves):
                    _, score = self.minimax(m, depth, alpha, beta)
                    if score > bestScore:
                        bestScore = score
                        move = m
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
                        move = m
                    beta = min(beta, bestScore)
                    if beta <= alpha:
                        break

        self.transposition_table[self.board.incremental_zobrist_hash] = (move, bestScore, depth)
        if depth > 0:
            self.board.pop()
        return move, bestScore


    def board_score(self):
        '''
        Evaluate the current board
        Using weighted linear combination of features on the chess board

        Note: values are absolute: must be cahnged relative to player for negamax framework
        TODO: Adjust values appropriately
        '''
        
        score = 0
        for t in chess.PIECE_TYPES:
            score += PIECE_VALUES[t-1] * len(self.board.pieces(t, chess.WHITE))
            score -= PIECE_VALUES[t-1] * len(self.board.pieces(t, chess.BLACK))

        pawnScore = 0
        for color in chess.COLORS:
            for pawn in self.board.pieces(chess.PAWN, color):
                i = chess.file_index(pawn)
                if len(self.board.pieces(chess.PAWN, color) & chess.BB_FILES[i]) >= 2:
                    pawnScore -= 0.05 #Note: this value gets added for each pawn that is part of the double up

                if i > 0 and i < 7:
                    neighborFiles = chess.BB_FILES[i-1] | chess.BB_FILES[i+1]
                elif i == 0:
                    neighborFiles = chess.BB_FILES[i+1]
                elif i == 7:
                    neighborFiles = chess.BB_FILES[i-1]
                neighborFiles = chess.SquareSet(neighborFiles)

                if len(self.board.pieces(chess.PAWN, color) & neighborFiles) == 0:
                    pawnScore -= 0.1

                forwardRanks = chess.SquareSet()
                if color:
                    for j in range(chess.rank_index(pawn) + 1, 7):
                        forwardRanks = forwardRanks | chess.BB_RANKS[j]
                else:
                    for j in range(chess.rank_index(pawn) - 1):
                        forwardRanks = forwardRanks | chess.BB_RANKS[j]
                pastZone = (neighborFiles | chess.BB_FILES[i]) & forwardRanks

                #TODO: add value to further past pawns
                if len(self.board.pieces(chess.PAWN, not color) & pastZone) == 0:
                    pawnScore += 0.2
                    
            score += pawnScore if color else -pawnScore
        

        #Bishop Pair Bonus
        if len(self.board.pieces(chess.BISHOP, chess.WHITE)) == 2:
            score += 0.3
        if len(self.board.pieces(chess.BISHOP, chess.BLACK)) == 2:
            score -= 0.3
            
        #TODO: King safety
        #This does not work at all since the position from gui is given without moves
            #Nevermind, it should work since the stack is formed in the minimax tree exploration
            #I am pretty sure it is not adding the scores as it should
        '''
        #Castling did not work out. REWORK
        whiteCastleMoves = [chess.Move.from_uci('e1g1'), chess.Move.from_uci('e1c1')]
        blackCastleMoves = [chess.Move.from_uci('e8g8'), chess.Move.from_uci('e8c8')]
        for m in whiteCastleMoves:
            if m in self.board.move_stack:
                score += 50
                print('WHITE CASTLE IMMANENT')
        for m in blackCastleMoves:
            if m in self.board.move_stack:
                score -= 50
        '''
            
        #TODO: Offense
        #TODO: Piece Square table (Knights and pawns in center, rooks on open files)
        #TODO: Defense
            
        #Options (Mobility)
        #Note: bugs might be caused by switching board turn
        if self.board.turn:
            score += len(self.board.legal_moves) * 0.001
            self.board.turn = not self.board.turn
            score -= len(self.board.legal_moves) * 0.001
            self.board.turn = not self.board.turn
        else:
            score -= len(self.board.legal_moves) * 0.001
            self.board.turn = not self.board.turn
            score += len(self.board.legal_moves) * 0.001
            self.board.turn = not self.board.turn
        
            
        #TODO: Tapered evaluation: different evaluation function for different times in game
        #TODO: Endgame tables
        #print("Board scored: {}".format(materialScore))
        return score


if __name__ == "__main__":
    ai = AI()
    while(1):
        inStr = sys.stdin.readline()
        command = None
        if inStr:
            command = inStr.split()[0]
        
        if command == "uci":
            sys.stdout.write("id name Cow Chess"+'\n')
            
            sys.stdout.write("id author Nick Collins!"+'\n')
            
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

        elif command == "eval": #NOT UCI, just debugging
            print('Current board score: {}'.format(ai.board_score()))
