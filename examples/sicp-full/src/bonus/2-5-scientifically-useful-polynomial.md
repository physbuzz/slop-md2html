# Scientifically Useful Polynomial Algorithms

## Polynomial Rootfinding

- Use a simple rootfinding algorithm to render algebraic number starscapes
- Include an algebraic number starscape picture
- Partial fraction decomposition is now trivial

## Fast polynomial multiplication
Implement the algorithm at:

https://www.youtube.com/watch?v=h7apO7q16V0

## Series expansion of rational functions

- Algorithm to generate the nth-term of a rational function expansion
- Berlekamp-Massey and Bostan-Mori? https://mzhang2021.github.io/cp-blog/berlekamp-massey/ https://codeforces.com/blog/entry/61306 https://codeforces.com/blog/entry/111862
- Interesting problems in the links above. At the very leasy cover the relation of a rational function to the Fibonacci sequence.

## Combinatorics results
- Algorithm to generate 

Results from ChatGPT that needs cross-referencing:

```
| label  | problem statement (length $n$)                                                                                                                                      | digraph size                               | OGF $F(x)$ (feel free to derive as exercise) | why it’s fun                                                                                                              |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **R1** | binary strings with no **consecutive 1s**                                                                                                                           | 2 states                                   | $\displaystyle\frac{1}{1-x-x^{2}}$           | classic Fibonacci; good sanity test for code                                                                              |
| **R2** | words over $\{0,1\}$ avoiding the pattern **1011**                                                                                                                  | 4 states                                   | $\displaystyle\frac{1-x^{4}}{1-2x+2x^{4}}$   | order-4 recurrence—already unpleasant by hand for $n\approx 10^6$                                                         |
| **R3** | **bounded-height Motzkin** walks: steps $\{-1,0,1\}$ never dropping below 0 and never rising above height 4                                                         | 5 × 5 transfer matrix                      | $\dfrac{P(x)}{Q(x)}$ with $\deg Q=5$         | first time Dyck-like paths yield **rational** instead of Catalan-type algebraic, and coefficients explode combinatorially |
| **R4** | tilings of a $2\times n$ strip with dominoes **and** monominoes but forbidding vertical $\;\boxed{\begin{smallmatrix}\_\\\_\end{smallmatrix}}\;$ gaps of length > 2 | 7 states (encode rightmost column profile) | order-7 recurrence                           | great illustration of transfer-matrix technique + shows power of programmatic enumeration                                 |

5 Good references / problem sources
Flajolet & Sedgewick – Analytic Combinatorics, §2.3 (regular languages → rational OGFs) and §4.1 (Bostan–Mori).

R. Stanley – Enumerative Combinatorics I: Exercises 1.98, 2.36, 2.37 are perfect rationals. Solutions manual outlines transfer matrices.

Herbert Wilf – generatingfunctionology, Chs. 2–3 for gentle warm-ups; §2.6 already derives R2‐style forbidden-word examples.

M. Bóna – A Walk Through Combinatorics, Ch. 10 “The Transfer-Matrix Method” supplies lattice-strip tiling tasks much harder than R1 but still rational.

N. Bostan’s lecture notes〈free online〉 give pseudocode for the Bostan–Mori algorithm and Maple implementations.

If you want lots of exercises with automata: S. Lando – Lectures on Generating Functions has a full chapter of “counting words avoiding…”.
```

In particular I'd be interested in the connection of the transfer matrix method I know and love from the Ising and Potts models, to this phrasing and emphasis of rational functions.


## Pade approximations
 - The algorithm
 - Algebraic approximations for pi (ie expand tan(z))
 - Find the asymptotics of random walks and self-avoiding walks

n-queens should fail, but chatgpt says these might work:
 - Non-attacking rook placements → clean combinatorics, rational generating functions.
 - Domino tilings of rectangles → known recursions, matchings on graphs.
 - Catalan-type sequences → rational or algebraic generating functions.

Allegedly matrix exponentials relate to pade approximants:
https://arxiv.org/pdf/2404.12789
