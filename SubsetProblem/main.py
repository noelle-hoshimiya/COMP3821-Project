import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator

from itertools import combinations

import sys
import io
 

class SubsetSum:
    def __init__(self, numbers, target):
        self.numbers = numbers
        self.target = target
        self.n = len(numbers)
        self.grover_calls = 0

        # Use traditional method to write f(x) in oracle operator instead since
        # we only care about how Grover works here.

        self.solutions = []
        for i in range(2 ** self.n):
            bitmask = format(i, f'0{self.n}b')
            subset = [numbers[j] for j in range(self.n) if bitmask[self.n-1-j] == '1']
            if sum(subset) == target:
                self.solutions.append(bitmask)
        self.num_solutions = len(self.solutions)

    def init_state(self, qc):
        for i in range(self.n):
            qc.h(i)
        qc.barrier()


    def oracle(self, qc):
        for solution in self.solutions:
            
            for i in range(self.n):
                if solution[self.n-1-i] == '0':
                    qc.x(i)
            
            # MCZ = H.MCX.H
            if self.n == 1:
                qc.z(0)
            elif self.n == 2:
                qc.cz(0, 1)
            else:
                qc.h(self.n-1)
                qc.mcx(list(range(self.n-1)), self.n-1)
                qc.h(self.n-1)
            
            for i in range(self.n):
                if solution[self.n-1-i] == '0':
                    qc.x(i)
        
        qc.barrier()

    def diffusion(self, qc):

        for i in range(self.n):
            qc.h(i)
        
        for i in range(self.n):
            qc.x(i)
        
        if self.n == 1:
            qc.z(0)
        elif self.n == 2:
            qc.cz(0, 1)
        else:
            qc.h(self.n-1)
            qc.mcx(list(range(self.n-1)), self.n-1)
            qc.h(self.n-1)
        
        for i in range(self.n):
            qc.x(i)
        
        for i in range(self.n):
            qc.h(i)
        
        qc.barrier()

    def grover_iteration(self, qc):
        self.grover_calls += 1
        self.oracle(qc)
        self.diffusion(qc)

    def solve(self, shots=1024, output_file = None):
        N = 2 ** self.n
        M = self.num_solutions
        if M == 0:
            return None
        iterations = int(np.pi / 4 * np.sqrt(N/M))

        qc = QuantumCircuit(self.n, self.n)

        self.init_state(qc)

        for _ in range(iterations):
            self.grover_iteration(qc)

        qc.measure(range(self.n), range(self.n))

        simulator = AerSimulator()
        job = simulator.run(qc, shots=shots)
        result = job.result()
        counts = result.get_counts()

        # Output

        output = []

        output.append(f"Test instance:")
        output.append(f"Numbers: {self.numbers}")
        output.append(f"Target: {self.target}")
        output.append(f"N={N}, M={M}")
        output.append(f"Iterations: {iterations}")

        output.append(f"\nResults:")
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        success_count = 0
        
        for bitstring, count in sorted_counts:
            subset = [self.numbers[j] for j in range(self.n) if bitstring[self.n-1-j] == '1']
            subset_sum = sum(subset)
            marker = "√" if subset_sum == self.target else "X"
            output.append(f"{marker}  {bitstring}: {count:4d} times  ->  {subset} = {subset_sum}")
            
            if subset_sum == self.target:
                success_count += count
        
        accuracy = success_count / shots * 100
        output.append(f"\nAccuracy: {accuracy:.2f}% ({success_count}/{shots})")
        output.append(f"Grover Call {self.grover_calls} Times")
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output))

        print('\n'.join(output))

        # qc.draw('mpl', filename='circuit.png')

        return qc, counts
    
if __name__ == "__main__":
    numbers = [1,2,3,4,5]
    target = 1

    solver = SubsetSum(numbers, target)
    circuit, counts = solver.solve(4096, "3.txt")
