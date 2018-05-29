import chess
from heapq import heappush, heappop


class Seminar1:

    black_pieces = {'P', 'N', 'B', 'R', 'Q', 'K'}
    white_pieces = {'p', 'n', 'b', 'r', 'q', 'k'}

    no_upper_row = 72057594037927935
    no_bottom_row = 18446744073709551360
    no_right_column = 18374403900871474942
    no_left_column = 9187201950435737471

    upper_row = 18374686479671623680
    bottom_row = 255

    def __init__(self):
        self.visited = {}
        self.priority_nodes = []
        self.king_position = 0
        self.player = False
        self.g_weight = 0
        self.operation_counter = 0
        self.move_count = 0
        self.mate_fields_weight = 1.5
        self.promotion_weight = 1
        self.enemy_count_weight = 0.3
        self.king_attack = 0

    def promotion_potential(self, moves_left, peasants, enemy_pieces, other_player_pieces):
        promotions = 0

        temp_peasants = peasants

        for i in range(moves_left):
            empty_squares = ~temp_peasants & ~other_player_pieces & ~enemy_pieces
            if self.player:
                peasant_moves = (temp_peasants << 8) & empty_squares
                left_peasant_attacks = (temp_peasants << 8) << 1
                right_peasant_attacks = (temp_peasants << 8) >> 1
            else:
                peasant_moves = (temp_peasants >> 8) & empty_squares
                left_peasant_attacks = (temp_peasants >> 8) << 1
                right_peasant_attacks = (temp_peasants >> 8) >> 1

            left_peasant_attacks &= self.no_right_column
            left_peasant_attacks &= enemy_pieces

            right_peasant_attacks &= self.no_left_column
            right_peasant_attacks &= enemy_pieces

            peasant_moves &= ~self.king_attack
            left_peasant_attacks &= ~self.king_attack
            right_peasant_attacks &= ~self.king_attack

            temp_peasants = peasant_moves | left_peasant_attacks | right_peasant_attacks

            if self.player:
                moves_promotion = peasant_moves & self.upper_row
                left_promotion = left_peasant_attacks & self.upper_row
                right_promotion = right_peasant_attacks & self.upper_row

                temp_peasants &= self.no_upper_row
            else:
                moves_promotion = peasant_moves & self.bottom_row
                left_promotion = left_peasant_attacks & self.bottom_row
                right_promotion = right_peasant_attacks & self.bottom_row

                temp_peasants &= self.no_bottom_row

            promotions += bin(moves_promotion).count('1') + bin(left_promotion).count('1') + bin(right_promotion).count('1')
        return promotions

    def mate_fields_covered(self, board):
        fields_covered = 0
        king_pos_tuple = self.num_to_tuple(self.king_position)
        for i in range(max(0, king_pos_tuple[0] - 1), min(7, king_pos_tuple[0] + 1)):
            for j in range(max(0, king_pos_tuple[1] - 1), min(7, king_pos_tuple[1] + 1)):
                fields_covered += len(board.attackers(self.player, self.tuple_to_num((i, j))))
        return fields_covered

    @staticmethod
    def enemy_piece_count(enemy_pieces):
        return bin(enemy_pieces).count('1')

    def calculate_h(self, board, moves_left, peasants, enemy_pieces, other_player_pieces):
        mate_fields_h = self.mate_fields_covered(board)
        promotion_potential_h = self.promotion_potential(moves_left, peasants, enemy_pieces, other_player_pieces)
        h = -self.mate_fields_weight * mate_fields_h \
            - self.promotion_weight * promotion_potential_h \
            + self.enemy_count_weight * self.enemy_piece_count(enemy_pieces)
        return h

    def add_new_moves(self, board, moves, g, path, start_peasants, start_enemy_pieces, start_other_player_pieces):
        for move in moves:
            peasants = start_peasants
            enemy_pieces = start_enemy_pieces
            other_player_pieces = start_other_player_pieces
            board.push(move)
            fen = board.fen()
            short_fen = fen.split(' ')[0]
            new_path = path + self.move_to_str(move) + ';'
            if short_fen in self.visited and self.visited[short_fen] <= g:
                board.pop()
                continue
            else:
                self.visited[short_fen] = g

            if g == self.move_count:
                if board.is_checkmate():
                    return new_path[:-1]
                else:
                    board.pop()
                    continue

            if board.is_check():
                board.pop()
                continue

            # ------------- binary board update -------------
            # updates enemy pieces
            enemy_pieces &= ~(1 << move.to_square)
            # updates player peasants
            if (1 << move.from_square) & peasants:
                peasants &= ~(1 << move.from_square)
                peasants |= (1 << move.to_square)
                if move.promotion:
                    peasants &= ~(1 << move.to_square)
                    other_player_pieces |= (1 << move.to_square)
            # updates other player pieces
            if (1 << move.from_square) & other_player_pieces:
                other_player_pieces &= ~(1 << move.from_square)
                other_player_pieces |= (1 << move.to_square)
            # ------------------------------------------------

            moves_left = self.move_count - g
            h = self.calculate_h(board, moves_left, peasants, enemy_pieces, other_player_pieces)
            priority = (g * self.g_weight) + h
            self.operation_counter += 1

            heappush(self.priority_nodes, [priority, self.operation_counter,
                                           {'fen': self.fix_fen(short_fen),
                                            'g': g,
                                            'path': new_path,
                                            'peasants': peasants,
                                            'enemy_pieces': enemy_pieces,
                                            'other_player_pieces': other_player_pieces}])
            board.pop()
        return None

    @staticmethod
    def tuple_to_num(tup):
        return tup[1] * 8 + tup[0]

    @staticmethod
    def num_to_tuple(num):
        return num % 8, num // 8

    def fix_fen(self, fen):
        color = ' w ' if self.player else ' b '
        return fen + color + '- - 0 1'

    @staticmethod
    def fix_start_fen(fen):
        return fen[:-1] + '- - 0 1'

    @staticmethod
    def move_to_str(move):
        move_str = chess.Move.uci(move)
        return move_str[:2] + '-' + move_str[2:]

    def solve(self, fen):
        self.__init__()
        self.move_count = int(fen[-1])
        fen = self.fix_start_fen(fen)

        board = chess.Board()
        board.set_fen(fen)
        self.player = board.turn
        self.king_position = board.king(not self.player)

        # ------------- calculates binary board status -------------
        enemy_pieces = 0
        peasants = 0
        other_player_pieces = 0
        for key, value in board.piece_map().items():
            if self.player and str(value) in self.white_pieces or not self.player and str(value) in self.black_pieces:
                enemy_pieces |= 1 << key
            if self.player and str(value) == 'P' or not self.player and str(value) == 'p':
                peasants |= 1 << key
            elif self.player and str(value) in self.black_pieces or not self.player and str(value) in self.white_pieces:
                other_player_pieces |= 1 << key

        # sets the squares, where the peasant attaks the king
        if self.player:
            left_king_attack = ((1 << self.king_position) >> 8) << 1
            right_king_attack = ((1 << self.king_position) >> 8) >> 1
        else:
            left_king_attack = ((1 << self.king_position) << 8) << 1
            right_king_attack = ((1 << self.king_position) << 8) >> 1
        left_king_attack &= self.no_right_column
        right_king_attack &= self.no_left_column
        self.king_attack = left_king_attack | right_king_attack
        # ----------------------------------------------------------

        heappush(self.priority_nodes, [0, 0, {'fen': fen,
                                              'g': 0,
                                              'path': '',
                                              'peasants': peasants,
                                              'enemy_pieces': enemy_pieces,
                                              'other_player_pieces': other_player_pieces}])
        while len(self.priority_nodes) > 0:
            node = heappop(self.priority_nodes)[2]
            board.set_fen(node['fen'])
            legal_moves = list(board.legal_moves)
            solution = self.add_new_moves(board, legal_moves, node['g']+1, node['path'],
                                          node['peasants'], node['enemy_pieces'], node['other_player_pieces'])
            if solution:
                print(solution)
                return solution

