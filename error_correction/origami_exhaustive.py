import numpy as np
from functools import reduce
from collections import Counter
from itertools import combinations
import threading
import os
import logging
import math

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


class Origami:
    """
    
    
    """

    def __init__(self, parity_bit_per_origami,
                 data_bit_per_origami, verbose=False):
        # Hardcoded parameter
        self.row = 6
        self.column = 8
        self.checksum_bit_per_origami = 4
        # Parameter from arguments
        self.verbose = verbose

        self.encoded_matrix = None
        self.recovered_matrix_info = []
        self.list_of_error_combination = []
        self.number_of_combination_done = [0]  # Putting zero at the beginning as while compare it won't show any error

        self.matrix_details, self.parity_bit_relation, self.checksum_bit_relation = \
            self._matrix_details(data_bit_per_origami, parity_bit_per_origami)
        # Calculate reverse relations of data bit with respect to parity bit.
        self.data_bit_to_parity_bit = Origami.data_bit_to_parity_bit(self.parity_bit_relation)
        self.orientation_details = {
            '0': 'Matrix was not flipped in any direction',
            '1': 'Matrix was flipped in horizontal direction. The bit was reversed',
            '2': 'Matrix was flipped in vertical direction. The bit was upside down',
            '3': 'Matrix was flipped in both horizontal and vertical direction. '
                 'The bit was both upside down and reversed'
        }

    def _matrix_details(self, data_bit_per_origami, parity_bit_per_origami):
        """
        Returns the relationship of the matrix. Currently all the the relationship is hardcoded.
        This method returns the following details:
            parity bits: 16/20 bits (user input)
            indexing bits: 4 bits (user input)
            orientation bits: 4 bits
            checksum bits: 4 bits
            data bits: 48 - parity bits(16/20) - orientation bits(4) - checksum bits(4) - indexing bits(userinput)
        :param data_bit_per_origami: How many bits of data will be encoded in per origami
        :param parity_bit_per_origami: How many bits of parity will be used in per origami
        :return: Relationships of the matrix
        """
        if parity_bit_per_origami == 16:
            # Will be removed soon enought
            data_index = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (2, 7),
                          (3, 7), (5, 7), (5, 6), (5, 5), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0),
                          (3, 0), (2, 0), (2, 2), (2, 5), (3, 2), (3, 5)]
            parity_bit_relation = {
                (1, 1): [(0, 0), (0, 1), (0, 2), (0, 7), (1, 0), (2, 0), (2, 2), (2, 5), (5, 1), (5, 7)],
                (1, 2): [(0, 1), (0, 3), (1, 7), (2, 3), (2, 5), (3, 2), (3, 4), (4, 7), (5, 0), (5, 5)],
                (1, 3): [(0, 1), (0, 3), (0, 4), (0, 5), (2, 7), (3, 0), (3, 3), (3, 7), (4, 0), (5, 4)],
                (1, 4): [(0, 2), (0, 3), (0, 4), (0, 6), (2, 0), (3, 0), (3, 4), (3, 7), (4, 7), (5, 3)],
                (1, 5): [(0, 4), (0, 6), (1, 0), (2, 2), (2, 4), (3, 3), (3, 5), (4, 0), (5, 2), (5, 7)],
                (1, 6): [(0, 0), (0, 5), (0, 6), (0, 7), (1, 7), (2, 2), (2, 5), (2, 7), (5, 0), (5, 6)],
                (2, 1): [(0, 2), (0, 3), (0, 5), (0, 6), (0, 7), (2, 0), (2, 3), (3, 3), (3, 5), (4, 0)],
                (2, 6): [(0, 0), (0, 1), (0, 2), (0, 4), (0, 5), (2, 4), (2, 7), (3, 2), (3, 4), (4, 7)],
                (3, 1): [(1, 0), (2, 3), (2, 5), (3, 0), (3, 3), (5, 2), (5, 3), (5, 5), (5, 6), (5, 7)],
                (3, 6): [(1, 7), (2, 2), (2, 4), (3, 4), (3, 7), (5, 0), (5, 1), (5, 2), (5, 4), (5, 5)],
                (4, 1): [(0, 1), (0, 7), (3, 0), (3, 2), (3, 5), (4, 0), (5, 0), (5, 1), (5, 2), (5, 7)],
                (4, 2): [(0, 0), (0, 5), (1, 7), (2, 2), (2, 4), (3, 3), (3, 5), (4, 7), (5, 1), (5, 3)],
                (4, 3): [(0, 4), (1, 0), (2, 0), (2, 3), (2, 7), (3, 7), (5, 1), (5, 3), (5, 4), (5, 5)],
                (4, 4): [(0, 3), (1, 7), (2, 0), (2, 4), (2, 7), (3, 0), (5, 2), (5, 3), (5, 4), (5, 6)],
                (4, 5): [(0, 2), (0, 7), (1, 0), (2, 3), (2, 5), (3, 2), (3, 4), (4, 0), (5, 4), (5, 6)],
                (4, 6): [(0, 0), (0, 6), (3, 2), (3, 5), (3, 7), (4, 7), (5, 0), (5, 5), (5, 6), (5, 7)]
            }
        elif parity_bit_per_origami == 20:
            # Data following indices of the matrix contains the data and indexes of the origami
            data_index = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (2, 7), (3, 7),
                          (5, 7), (5, 6), (5, 5), (5, 4), (5, 3), (5, 2), (5, 1), (5, 0), (3, 0), (2, 0)]
            parity_bit_relation = {
                (1, 1): [(0, 0), (0, 1), (0, 5), (2, 3), (5, 4)],
                (1, 2): [(0, 1), (0, 3), (1, 0), (2, 4), (2, 7)],
                (1, 3): [(0, 0), (0, 2), (0, 4), (3, 7), (5, 2)],
                (1, 4): [(0, 3), (0, 5), (0, 7), (3, 0), (5, 5)],
                (1, 5): [(0, 4), (0, 6), (1, 7), (2, 0), (2, 3)],
                (1, 6): [(0, 2), (0, 6), (0, 7), (2, 4), (5, 3)],
                (2, 1): [(1, 0), (2, 3), (3, 0), (4, 7), (5, 0), (5, 3)],
                (2, 6): [(1, 7), (2, 4), (3, 7), (4, 0), (5, 4), (5, 7)],
                (3, 1): [(0, 0), (0, 3), (1, 7), (2, 0), (3, 3), (4, 0)],
                (3, 6): [(0, 4), (0, 7), (1, 0), (2, 7), (3, 4), (4, 7)],
                (4, 1): [(0, 4), (3, 3), (5, 0), (5, 1), (5, 5)],
                (4, 2): [(3, 4), (3, 7), (4, 0), (5, 1), (5, 3)],
                (4, 3): [(0, 2), (2, 7), (5, 0), (5, 2), (5, 4)],
                (4, 4): [(0, 5), (2, 0), (5, 3), (5, 5), (5, 7)],
                (4, 5): [(3, 0), (3, 3), (4, 7), (5, 4), (5, 6)],
                (4, 6): [(0, 3), (3, 4), (5, 2), (5, 6), (5, 7)],
                (2, 2): [(0, 2), (1, 0), (2, 0), (5, 6), (5, 0)],
                (2, 5): [(0, 5), (1, 7), (2, 7), (5, 1), (5, 7)],
                (3, 2): [(0, 6), (3, 0), (4, 0), (5, 2), (0, 0)],
                (3, 5): [(0, 1), (3, 7), (4, 7), (5, 5), (0, 7)]
            }

        matrix_details = dict(
            data_bits=data_index[:data_bit_per_origami],
            orientation_bits=[(1, 0), (1, 7), (4, 0), (4, 7)],
            indexing_bits=data_index[data_bit_per_origami:],
            checksum_bits=[(2, 3), (2, 4), (3, 3), (3, 4)],
            orientation_data=[1, 1, 1, 0]
        )
        checksum_bit_relation = {
            (2, 3): [(0, 0), (0, 2), (1, 7), (2, 0), (5, 3), (5, 6)],
            (2, 4): [(0, 5), (0, 7), (1, 0), (2, 7), (5, 1), (5, 4)],
            (3, 3): [(0, 3), (0, 6), (3, 0), (4, 7), (5, 0), (5, 2)],
            (3, 4): [(0, 1), (0, 4), (3, 7), (4, 0), (5, 5), (5, 7)]
        }

        return matrix_details, parity_bit_relation, checksum_bit_relation

    def create_initial_matrix_from_binary_stream(self, binary_stream, index):
        """
        Put the binary data and indexing in the matrix.
        :param binary_stream: Binary data that need to be encoded in the matrix
        :param index: Indexing of hte matrix
        :return: Matrix with data and indexing
        """
        binary_list = list(binary_stream)
        data_matrix = np.full((self.row, self.column), -1)  # All the cell of the matrix will have initial value -1.
        # Putting the data into matrix
        for i, bit_index in enumerate(self.matrix_details["data_bits"]):
            data_matrix[bit_index[0]][bit_index[1]] = binary_list[i]
        # Putting orientation data
        for i, bit_index in enumerate(self.matrix_details["orientation_bits"]):
            data_matrix[bit_index[0]][bit_index[1]] = self.matrix_details['orientation_data'][i]
        # Putting indexing bits.
        if index >= 2 ** len(self.matrix_details["indexing_bits"]):  # Checking if current index is more than supported.
            logging.error(
                'Maximum support index is {maximum_input}. But given index is {index}'.format(
                    maximum_input=2 ** len(self.matrix_details["indexing_bits"]),
                    index=index
                ))
            raise ValueError("Maximum support of index exceed")
        index_len = '0' + str(len(self.matrix_details["indexing_bits"])) + 'b'
        index_bin = list(format(index, index_len))
        # Set the indexing
        for i, bit_index in enumerate(self.matrix_details["indexing_bits"]):
            data_matrix[bit_index[0]][bit_index[1]] = index_bin[i]

        return data_matrix

    def _xor_matrix(self, matrix, relation):
        """
        XOR the data using the relation
        :param matrix: Matrix upon which xor will be implemented
        :param relation: Relation of xor data
        :return: Matrix with xor
        """
        for single_xor_relation in relation:
            # Getting the all the data bits related to a specific parity bit
            data_bits_value = [int(matrix[a[0]][a[1]]) for a in
                               relation[single_xor_relation]]
            # XORing all the data bits
            xored_value = reduce(lambda i, j: int(i) ^ int(j), data_bits_value)
            # Update the parity bit with the xored value
            matrix[single_xor_relation[0]][single_xor_relation[1]] = int(xored_value)

        return matrix

    def _encode(self, binary_stream, index):
        """
        Handle the encoding. Most of the time handle xoring.
        :param binary_stream: Binary value of the data
        :param index: Index of the current matrix
        :return: Encoded matrix
        """
        # Create the initial matrix which will contain the word,index and binary bits for fixing orientation but no
        # error encoding. So the parity bits will have the initial value of -1
        encoded_matrix = self.create_initial_matrix_from_binary_stream(binary_stream, index)
        # Set the cell value in checksum bits. This has to be before the parity bit xoring. Cause the parity bit
        # contains the checksum bits. And the default value of the checksum bit is -1. So if the parity xor happens
        # before checksum xor then some of the parity bit will have value negative. as that would be xor with -1
        encoded_matrix = self._xor_matrix(encoded_matrix, self.checksum_bit_relation)
        # XOR for the parity code
        encoded_matrix = self._xor_matrix(encoded_matrix, self.parity_bit_relation)
        return self.matrix_to_data_stream(encoded_matrix)

    @staticmethod
    def data_bit_to_parity_bit(parity_bit_relation):
        """
        Reverse the parity bit to data bit.
        :param parity_bit_relation: A dictionary that contains parity bit as key and
         the respective indices that will be xored in the parity bit as value.
        :return: A dictionary that contains indices as key and and respective parity
         indices that used that indices for xoring.
        """
        data_bit_to_parity_bit = {}
        for single_parity_bit in parity_bit_relation:
            # Loop through each parity bit relation and add those
            for single_data_bit in parity_bit_relation[single_parity_bit]:
                data_bit_to_parity_bit.setdefault(single_data_bit, []).append(single_parity_bit)
        return data_bit_to_parity_bit

    def show_encoded_matrix(self):
        """
        Display encoded matrix

        Returns:
            None
        """
        self.print_matrix(self.encoded_matrix)

    @staticmethod
    def print_matrix(matrix, in_file=False):
        """
        Display a given matrix
        
        Parameters:
            matrix: A 2-D matrix
            
        Returns:
            None
        """
        for row in range(len(matrix)):
            for column in range(len(matrix.T)):
                if not in_file:
                    print(matrix[row][column], end="\t")
                else:
                    print(matrix[row][column], end="\t", file=in_file)
            if not in_file:
                print("")
            else:
                print("", file=in_file)

    @staticmethod
    def matrix_to_data_stream(matrix):
        """
        Convert 2-D matrix to one dimensional string
        
        Parameters:
            matrix: A 2-D matrix
            
        Returns:
            data_stream: string of 2-D matrix
        """
        data_stream = []
        for row in range(len(matrix)):
            for column in range(len(matrix.T)):
                data_stream.append(matrix[row][column])
        return ''.join(str(i) for i in data_stream)

    def data_stream_to_matrix(self, data_stream):
        """
        Convert a sting to 2-D matrix
        
        The length of data stream should be 48 bit currently this algorithm is only working with 8*6 matrix
        
        Parameters:
            data_stream: 48 bit of string
        
        Retruns:
            matrix: return 2-D matrix
        """
        matrix = np.full((self.row, self.column), -1)
        data_stream_index = 0
        for row in range(len(matrix)):
            for column in range(len(matrix.T)):
                matrix[row][column] = data_stream[data_stream_index]
                data_stream_index += 1
        return matrix

    def fix_orientation(self, matrix, option=0):
        """
        Fix the orientation of the decoded matrix
        
        If fixing orientation failed then returns the same matrix that was passed. But it will shows and error message in that case
        
        Parameters:
            matrix: Decoded matrix
            option: On which direction the matrix will be flipped now
        
        Returns:
            matrix: Orientation fixed matrix. 
        """
        # In this matrix the data (2,2),(2,3)(3,2) = 1 and(3,3) = 0 will be fixed to determine the orientation of the matrix
        # At first we are checking these position
        # First option is using current matrix
        # Second option is reversing the current matrix that will fix the vertically flipped issue
        # Third option is mirroring the current matrix that will fix the horizontally flipped issue
        # Fourth option is both reverse then mirror the current matrix that will fix both vertically flipped and horizontally flipped issue
        if option == 0:
            corrected_matrix = matrix
        elif option == 1:
            # We will just take the reverse/Flip in horizontal direction
            corrected_matrix = np.flipud(matrix)
        elif option == 2:
            # We will take the mirror/flip in vertical direction
            corrected_matrix = np.fliplr(matrix)
        elif option == 3:
            # Flip in both horizontal and vertical direction
            corrected_matrix = np.flipud(np.fliplr(matrix))
        else:
            # The orientation couldn't be determined
            # This is not correctly oriented. Will remove that after testing
            return -1, matrix
        orientation_check = True
        for i, bit_index in enumerate(self.matrix_details["orientation_bits"]):
            if corrected_matrix[bit_index[0]][bit_index[1]] != self.matrix_details["orientation_data"][i]:
                orientation_check = False
        if orientation_check:
            return option, corrected_matrix
        else:
            # Matrix isn't correctly oriented so we will try with other orientation
            return self.fix_orientation(matrix, option + 1)

    def find_possible_error_location(self, matrix):
        """
        Find the possible error location of the 2-D matrix
        
        Parameters:
            matrix: 2-D matrix
            
        Returns:
            correct_indexes: Indices of all correct parity bits
            incorrect_indexes: Indices of all incorrect parity bit
        """
        correct_indexes = []
        incorrect_indexes = []
        for parity_bit_index in self.parity_bit_relation:
            # Now xoring every element again and checking it's correct or not
            nearby_values = [int(matrix[a[0]][a[1]]) for a in self.parity_bit_relation[parity_bit_index]]
            xored_value = reduce(lambda i, j: int(i) ^ int(j), nearby_values)
            if matrix[parity_bit_index[0]][parity_bit_index[1]] == int(xored_value):
                correct_indexes.append(parity_bit_index)
            else:
                incorrect_indexes.append(parity_bit_index)
        return correct_indexes, incorrect_indexes

    def is_matrix_correct(self, matrix):
        """
        Check if all the bits of the matrix are correct or not

        Parameter:
            matrix: A 2-D matrix
        Returns:
            Boolean: True if matrix is correct false otherwise
        """
        correct_indexes, incorrect_indexes = self.find_possible_error_location(matrix)
        return len(incorrect_indexes) == 0

    def _decode(self, matrix, parity_bit_indexes_incorrect, common_parity_index, minimum_temporary_weight,
                maximum_number_of_error, false_positive, maximum_combination_check, orientation=-1):
        # We will try to decode multiple origami so we are making the variable empty at the first
        self.recovered_matrix_info = []
        if len(parity_bit_indexes_incorrect) > 0:
            # All the indices that is related to the incorrect parity bit
            probable_error_indexes = [j for i in parity_bit_indexes_incorrect for j in self.parity_bit_relation[i]]
            # All the indexes that is related to the unmatched checksum
            probable_error_from_checksum = []
            # Checksum indexes that didn't match after xoring it's related indices.
            unmatched_checksum = []
            for single_checksum_index, single_checksum_relation in self.checksum_bit_relation.items():
                nearby_values = [int(matrix[a[0]][a[1]]) for a in single_checksum_relation]
                xored_value = reduce(lambda i, j: int(i) ^ int(j), nearby_values)
                if matrix[single_checksum_index[0]][
                    single_checksum_index[1]] != xored_value:  # As it didn't match it might have some error
                    unmatched_checksum.append(single_checksum_index)
                    probable_error_indexes.append(single_checksum_index)
                    probable_error_from_checksum.extend(
                        single_checksum_relation)  # This will be the second parameter to order the error list
            # probable_error_index = [item for item in Counter(probable_error_indexes).most_common() if item[1] >= 3]
            # If the error also present in the probable checksum error then we will increase the number of occurance of these index
            # All Probable error indexes expect the checksum after checking the temporary weight.
            # Will contain { temporary_weight: [all indexes of same temporary weight] }
            probable_data_error = {}
            # Final parity error. After checking the temporary weight
            probable_parity_error = {}
            # Parity bit error that is taken from error data bit
            probable_parity_error_all = []
            # Putting the temporary weight on each data and checksum indexes.
            # The default temporary weight will be it's number of occurrence from unmatched parity error.
            for item in Counter(probable_error_indexes).most_common():
                if item[0] in probable_error_from_checksum and item[0] in unmatched_checksum:
                    temp_weight = item[1] + 4
                elif item[0] in probable_error_from_checksum:
                    temp_weight = item[1] + 2
                elif item[0] in unmatched_checksum:
                    temp_weight = item[1] + 2
                else:
                    temp_weight = item[1]
                # threshold_parity = item[1] + 1 if item[0] in probable_error_from_checksum else item[1]
                if temp_weight < minimum_temporary_weight:
                    break
                probable_data_error.setdefault(temp_weight, []).append(item[0])
                probable_parity_error_all.extend(self.data_bit_to_parity_bit[item[0]])

            probable_parity_error_all.extend(parity_bit_indexes_incorrect)
            # Putting temporary weight on each parity indexes.
            # The default temporary weight will be number of occurrence of the parity bit from the data bit
            # The temporary weight will add 10 more if the specific parity bit didn't match in the first palce.
            for item in Counter(probable_parity_error_all).most_common():
                temp_weight = item[1] + 10 if item[0] in parity_bit_indexes_incorrect else item[1]
                if temp_weight < common_parity_index:
                    break
                # The parity that have more temporary weight have high probability of error.
                probable_parity_error.setdefault(temp_weight, []).append(item[0])
            # Combine both data error and parity error
            # At First the highest point of data error will be added. Then highest point of parity error will be added
            # Sorting the two dictionary
            probable_data_error = sorted(probable_data_error.items(), key=lambda x: int(x[0]), reverse=True)
            probable_parity_error = sorted(probable_parity_error.items(), key=lambda x: int(x[0]), reverse=True)
            probable_error_index = []  # Contains all the error parity bit error + data bit error + checksum bit error
            total_false_positive_added = 0
            while len(probable_parity_error) > 0 or len(probable_data_error) > 0:
                if len(probable_data_error):
                    poped_indexes = probable_data_error.pop(0)[1]
                    for i in poped_indexes:
                        if matrix[i[0]][i[1]] == 1:
                            if false_positive > total_false_positive_added:
                                probable_error_index.append(i)
                                total_false_positive_added += 1
                        else:
                            probable_error_index.append(i)
                    # probable_error_index.extend(probable_data_error.pop(0)[1])
                if len(probable_parity_error):
                    # probable_error_index.extend(probable_parity_error.pop(0)[1])
                    poped_indexes = probable_parity_error.pop(0)[1]
                    for i in poped_indexes:
                        if matrix[i[0]][i[1]] == 1:
                            if false_positive > total_false_positive_added:
                                probable_error_index.append(i)
                                total_false_positive_added += 1
                        else:
                            probable_error_index.append(i)
            # Currently we have only one form of error. That bit 1 will be zero. zero will never be 1.
            # As per recent discovery this is not always the case so we are putting is this option as user parameter
            # So we are removing all the indexes that have value 1. Considering them as correct.
            # Process the false positive

            # if not false_positive:
            #     probable_error_index = [individual_index for individual_index in probable_error_index
            #                             if matrix[individual_index[0]][individual_index[1]] == 0]
            # If probable error is more than 24 then we will not try to fix that
            self.fix_error(matrix, probable_error_index, maximum_number_of_error, orientation,
                           maximum_combination_check)
        else:  # There are no error in the parity bit found so we will check the orientation and checksum only
            single_recovered_matrix = {}
            if orientation == -1:  # No orientation is given. We need to check orientation
                orientation_info, single_recovered_matrix['matrix'] = self.fix_orientation(matrix)
                if orientation_info == -1:
                    logging.info("Couldn't decode the matrix")
                    return -1
                single_recovered_matrix['orientation_details'] = self.orientation_details[str(orientation_info)]
                single_recovered_matrix['orientation'] = orientation_info
            else:  # Orientation is already given
                single_recovered_matrix['orientation_details'] = self.orientation_details[str(orientation)]
                single_recovered_matrix['orientation'] = orientation
                single_recovered_matrix['matrix'] = matrix
            single_recovered_matrix['total_probable_error'] = 0
            single_recovered_matrix['probable_error_locations'] = 0
            single_recovered_matrix['is_recovered'] = True
            single_recovered_matrix['orientation_fixed'] = True
            single_recovered_matrix['checksum_checked'] = self.check_checksum(single_recovered_matrix['matrix'])
            self.recovered_matrix_info.append(single_recovered_matrix)

        # If there is no recovered matrix will return -1.
        if len(self.recovered_matrix_info) == 0:
            return -1

        corrected_matrix = []

        for index, single_recovered_matrix in enumerate(self.recovered_matrix_info):
            if single_recovered_matrix['is_recovered'] and single_recovered_matrix['orientation_fixed'] and \
                    single_recovered_matrix["checksum_checked"]:
                # Extracting data and index from the matrix
                self.recovered_matrix_info[index]['index'], self.recovered_matrix_info[index]['binary_data'] = \
                    self.extract_text_and_index(self.recovered_matrix_info[index]["matrix"])
                # If verbose is true then print all the details
                if self.verbose:
                    # Print the matrix
                    print("Decoded matrix is: ")
                    self.print_matrix(single_recovered_matrix["matrix"])
                    # print("Recovered word : " + str(single_recovered_matrix["recovered_text"]))
                    print("Recovered index : " + str(single_recovered_matrix["index"]))
                    print("Total number of error is : " + str(single_recovered_matrix['total_probable_error']))
                    print("Error Locations : " + str(single_recovered_matrix['probable_error_locations']))
                    print("Orientation Information: " + (str(single_recovered_matrix["orientation_details"])))

                corrected_matrix.append(single_recovered_matrix)
        # Sort the matrix based on total probable error. The Lowest probable error will be return as corrected matrix.
        sorted_corrected_matrix = sorted(corrected_matrix, key=lambda x: x['total_probable_error'])
        return sorted_corrected_matrix[0]

    def extract_text_and_index(self, matrix):
        if matrix is None:
            return
        # Extracting index first
        index_bin = []
        for bit_index in self.matrix_details['indexing_bits']:
            index_bin.append(matrix[bit_index[0]][bit_index[1]])
        index_decimal = int(''.join(str(i) for i in index_bin), 2)
        # Extracting the text now
        # Extracting text index
        text_bin_data = ""
        for bit_index in self.matrix_details['data_bits']:
            text_bin_data += str(matrix[bit_index[0]][bit_index[1]])

        return index_decimal, text_bin_data

    def decode(self, data_stream, common_parity_index, minimum_temporary_weight,
               maximum_number_of_error, false_positive, maximum_combination_check, test=False):
        """
        Decode the given data stream into word and their respective index
        
        Parameters:
            data_stream: A string of 48 bit
            test: If test mode is True then it will return the possible error.
            Otherwise only recovered word and position of error
        
        Return:
            decoded_data: A dictionary of index and world which is the most possible solution
            :param test:
            :param minimum_temporary_weight:
            :param data_stream:
            :param common_parity_index:
            :param false_positive:
            :param maximum_number_of_error:
        """
        # If length of decoded data is not 48 then show error
        if len(data_stream) != 48:
            raise ValueError("The data stream length should be 48")
        # Initial check which parity bit index gave error and which gave correct results
        # Converting the data strem to data array first
        data_matrix_for_decoding = self.data_stream_to_matrix(data_stream)
        parity_bit_indexes_correct, parity_bit_indexes_incorrect = self.find_possible_error_location(
            data_matrix_for_decoding)
        return self._decode(data_matrix_for_decoding, parity_bit_indexes_incorrect, common_parity_index,
                            minimum_temporary_weight, maximum_number_of_error, false_positive,
                            maximum_combination_check, orientation=-1)

        #   After fixing orientation we need to check the checksum bit. If we check before orientation fixed then it will not work

        # sorting the matrix

    def check_checksum(self, matrix):
        for check_sum_bit in self.checksum_bit_relation:
            nearby_values = [int(matrix[a[0]][a[1]]) for a in self.checksum_bit_relation[check_sum_bit]]
            xor_value = reduce(lambda i, j: int(i) ^ int(j), nearby_values)
            if xor_value != matrix[check_sum_bit[0]][check_sum_bit[1]]:
                if self.verbose:
                    logging.info("Checksum did not matched");
                return False
        return True

    def nCr(self, n, r):
        f = math.factorial
        return int(f(n) / f(r) / f(n - r))

    def fix_with_different_combination(self, original_matrix, probable_error_index, orientation,
                                       maximum_combination_check,
                                       current_error_combination):

        if len(probable_error_index) > current_error_combination and self.nCr(len(probable_error_index),
                                                                              current_error_combination) > maximum_combination_check:
            if self.verbose:
                logging.info(
                    'Did not check error combination {current_error_combination}. Maximum error combination check is \
                    {maximum_combination_check} but {combination_given}\
                     combination was created'.format(
                        current_error_combination=current_error_combination,
                        maximum_combination_check=maximum_combination_check,
                        combination_given=self.nCr(len(probable_error_index), current_error_combination)
                    ))
            return

        for error_indexes in combinations(probable_error_index, current_error_combination):
            # If another thread sees that we already got a fixed matrix then this will stop execution here
            # If we get a corrected matrix from another thread that has less error than the running thread is
            # processing then we will return from this thread.
            if len(probable_error_index) > current_error_combination and self.nCr(len(probable_error_index),
                                                                                  current_error_combination) > maximum_combination_check:
                if self.verbose:
                    logging.info(
                        'Did not check error combination {current_error_combination}. Maximum error combination check\
                         is {maximum_combination_check} but {combination_given} combination was created'.format(
                            current_error_combination=current_error_combination,
                            maximum_combination_check=maximum_combination_check,
                            combination_given=self.nCr(len(probable_error_index), current_error_combination)
                        ))
                continue
            matrix = original_matrix.copy()
            for individual_error_index in error_indexes:
                if (int(matrix[individual_error_index[0]][individual_error_index[1]])) == 1:
                    matrix[individual_error_index[0]][individual_error_index[1]] = 0
                else:
                    matrix[individual_error_index[0]][individual_error_index[1]] = 1
            if self.is_matrix_correct(matrix):
                single_recovered_matrix = {}
                if orientation == -1:  # No orientation was given so we need to check that
                    orientation_info, matrix = self.fix_orientation(matrix)
                    if orientation_info == -1:
                        continue
                else:  # Orientation was given we don't need to double check that
                    orientation_info = orientation
                if self.check_checksum(matrix):
                    single_recovered_matrix['orientation_details'] = self.orientation_details[str(orientation_info)]
                    single_recovered_matrix['orientation'] = orientation_info
                    single_recovered_matrix['matrix'] = matrix
                    single_recovered_matrix['orientation_fixed'] = True
                    single_recovered_matrix['total_probable_error'] = len(error_indexes)
                    single_recovered_matrix['probable_error_locations'] = error_indexes
                    single_recovered_matrix['is_recovered'] = True
                    single_recovered_matrix['checksum_checked'] = True
                    self.recovered_matrix_info.append(single_recovered_matrix)
                    if self.verbose:
                        logging.info('Found a recovered matrix which had {current_error_combination} error'.format(
                            current_error_combination=current_error_combination
                        ))
                    return 1

    def fix_error(self, original_matrix, probable_error_index, maximum_number_of_error, orientation,
                  maximum_combination_check):
        """
        Try to alter the all the possible combination of error position
        
        Parameters:
            matrix: A 2-D matrix
            probable_error_index: Most probable error index that is return by method find_possible_error_location()
            
            Returns:
                error_corrected_matrix = A list of all possible matrix that is generated by altering the given error index
        """
        # First we will make all the possible combination of error
        # self.list_of_error_combination = list(range(1, len(probable_error_index) + 1))
        self.list_of_error_combination = list(range(1, maximum_number_of_error + 1))

        for current_error_combination in self.list_of_error_combination:
            if self.fix_with_different_combination(original_matrix, probable_error_index, orientation,
                                                maximum_combination_check, current_error_combination):
                return
            if self.verbose:
                logging.info('Error combination done : {current_error_combination}'.format(
                    current_error_combination=current_error_combination
                ))


if __name__ == "__main__":

    bin_stream = "0111010101100101"
    origami_object = Origami(20, 16, False)
    encoded_file = origami_object.data_stream_to_matrix(origami_object._encode(bin_stream, 0))
    print(encoded_file)
    # Insert error
    encoded_file[1][0] = 0
    encoded_file[1][7] = 0
    encoded_file[2][3] = 0
    # encoded_file = np.fliplr(encoded_file)

    decoded_file = origami_object.decode(origami_object.matrix_to_data_stream(encoded_file), 1, 2,
                                         8, False, 1000000, test=False)

    if not decoded_file == -1 and decoded_file['binary_data'] == bin_stream:
        print("Decoded successfully")
    else:
        print("wasn't decoded successfully")
