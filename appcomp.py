from flask import Flask, request, render_template, jsonify
import re
import heapq
from collections import defaultdict

app = Flask(__name__)

# Run-Length Encoding
def run_length_encoding_iterative(input_string):
    output = ''
    count = 1

    for i in range(1, len(input_string)):
        if input_string[i] == input_string[i - 1]:
            count += 1
        else:
            output += f"{input_string[i - 1]}:{count} "
            count = 1

    output += f"{input_string[-1]}:{count} "
    return output.strip()

# Run-Length Decompression
def run_length_decompression(compressed_string):
    output = ''
    parts = compressed_string.split()
    for part in parts:
        if ':' in part:
            char, count = part.split(':')
            if count.isdigit():
                output += char * int(count)
            else:
                return "Error: Invalid count value"
        else:
            return "Error: Invalid compressed string format"
    return output

# Arithmetic Coding
def arithmetic_encode(input_string, probabilities):
    low = 0.0
    high = 1.0

    for char in input_string:
        range_width = high - low
        high = low + range_width * probabilities[char][1]
        low = low + range_width * probabilities[char][0]

    return (low + high) / 2

def arithmetic_decode(encoded_value, probabilities, length):
    decoded_string = ""

    for _ in range(length):
        for char, (low, high) in probabilities.items():
            if low <= encoded_value < high:
                decoded_string += char
                range_width = high - low
                encoded_value = (encoded_value - low) / range_width
                break

    return decoded_string

def build_probability_table(probabilities):
    low = 0.0
    table = {}

    for char, prob in probabilities.items():
        high = low + prob
        table[char] = (low, high)
        low = high

    return table

# Helper functions for Huffman coding
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(frequencies):
    heap = [Node(char, freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0]

def generate_codes(node, prefix="", code_map={}):
    if node is not None:
        if node.char is not None:
            code_map[node.char] = prefix
        generate_codes(node.left, prefix + "0", code_map)
        generate_codes(node.right, prefix + "1", code_map)
    return code_map


# Routes for Arithmetic Coding
@app.route('/encode', methods=['POST'])
def encode():
    data = request.json
    input_string = data.get('input_string')
    probabilities = data.get('probabilities')

    if not input_string or not probabilities:
        return jsonify({'error': 'Invalid input: Both input string and probabilities are required.'}), 400

    try:
        prob_table = build_probability_table(probabilities)
        encoded_value = arithmetic_encode(input_string, prob_table)
        return jsonify({'encoded_value': encoded_value})
    except Exception as e:
        return jsonify({'error': f'Encoding failed: {str(e)}'}), 500

@app.route('/decode', methods=['POST'])
def decode():
    data = request.json
    encoded_value = data.get('encoded_value')
    probabilities = data.get('probabilities')
    length = data.get('length')

    if encoded_value is None or not probabilities or not length:
        return jsonify({'error': 'Invalid input: Encoded value, probabilities, and length are required.'}), 400

    try:
        prob_table = build_probability_table(probabilities)
        decoded_string = arithmetic_decode(encoded_value, prob_table, length)
        return jsonify({'decoded_string': decoded_string})
    except Exception as e:
        return jsonify({'error': f'Decoding failed: {str(e)}'}), 500


# Routes for Run-Length Encoding
@app.route('/compress', methods=['POST'])
def compress():
    user_input = request.json.get('input_string')
    if not user_input:
        return jsonify({'error': 'Empty input: Input string is required for compression.'}), 400

    try:
        result = run_length_encoding_iterative(user_input)
        return jsonify({'compressed': result})
    except Exception as e:
        return jsonify({'error': f'Compression failed: {str(e)}'}), 500


@app.route('/decompress', methods=['POST'])
def decompress():
    compressed_input = request.json.get('input_string')
    if not compressed_input:
        return jsonify({'error': 'Empty input: Compressed string is required for decompression.'}), 400

    if not re.match(r'^[A-Za-z]+:\d+( [A-Za-z]+:\d+)*$', compressed_input):
        return jsonify({'error': 'Invalid compressed string format: Expected format is "char:count".'}), 400

    try:
        result = run_length_decompression(compressed_input)
        return jsonify({'decompressed': result})
    except Exception as e:
        return jsonify({'error': f'Decompression failed: {str(e)}'}), 500


@app.route("/huffman/encode", methods=["POST"])
def huffman_encode():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    frequencies = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1

    root = build_huffman_tree(frequencies)
    codes = generate_codes(root)
    encoded_text = "".join(codes[char] for char in text)
    return jsonify({"encoded": encoded_text, "tree": codes})

# Main Route
@app.route('/')
def index():
    return render_template('index.html')

# Main
if __name__ == '__main__':
    app.run(debug=True)
