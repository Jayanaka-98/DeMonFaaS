from flask import Blueprint

compute_api = Blueprint('compute_api', __name__)

@compute_api.route(f'/computeapi/<limit>')
def sieve_of_eratosthenes(limit):
    # Create a boolean array "prime[0..limit]" and initialize all entries as True.
    # A value in prime[i] will finally be False if i is not a prime, else True.
    limit = int(limit)
    prime = [True for _ in range(limit + 1)]
    p = 2
    while p * p <= limit:
        # If prime[p] is not changed, then it is a prime
        if prime[p] is True:
            # Updating all multiples of p to not prime
            for i in range(p * p, limit + 1, p):
                prime[i] = False
        p += 1
    
    # Collecting all prime numbers
    primes = [p for p in range(2, limit) if prime[p]]
    return primes[0:10]