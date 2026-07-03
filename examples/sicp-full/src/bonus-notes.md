
@toc 
## Extras

Filling in stuff from [bonus-notes.md](bonus-notes.html) as time goes on. A lot of this is a big TODO. Anything with a ✯ next to it means it takes significant work.

- [Anki flashcards](anki.html)

**Ch1 Bonuses**

- Asymptotic approximations and some notes on $\Theta$, $\Omega$, $O$. **(~done)**
- The ill-fated Santa Barbara Monte Carlo machine
- Exact runtime of count-change
- Linear diophantine equations (using lists)
- Bonus special numbers and number theory (Euler totient, base b expansions of fractions, Lucas, Catalan, partition numbers, "negative binomial")

**Ch2 Bonuses**

 - ✯ Drawing Church numerals
 - The abstract algebra of 2-5 **(~pretty far)**
 - Actually useful polynomial algorithms **(~outlined)**
 - Story about polynomial long division + my grandpa (at least research it)

## Articles I decided not to work on:

**General stuff:**

- ✯ Racket crash course
- SICP Library Functions

**Ch1 runners up:**

- Iterated functions for numerical approximation. Following up on the iterated 
polynomial for approximating sine. There's also iteration for the 
Feigenbaum-cvitanovic functional equation. This is a great research project, 
not a great bonus chapter.
- Improving rates of convergence (newton, accelerated newton, successive averaging, resummation). Again we probably just want to work with a full plotting + 
CAS here.
- ✯ Challenge 3: Thoughts on reversibility and quantum computing. This is just a 
big independent project, not a good bonus chapter.

**Ch1 scrapped ideas:**

- RSA implementation
- ✯ Challenge 1: try to compute the Ramanujan tau function. This is some memoized code using recursion that supposedly works: [https://claude.ai/chat/374b1219-3cd8-4a9e-87a3-dfddfc1f8896](https://claude.ai/chat/374b1219-3cd8-4a9e-87a3-dfddfc1f8896), but simple mathematica code can generate it too: `CoefficientList[Take[Expand[Product[(1 - x^k)^24, {k, 1, 30}]], 30],x]`
- ✯ Challenge 2: Continued fraction expansion of pi or 1/pi using exact arithmetic.

**Ch2 scrapped ideas:**

- Enumerating binary trees and arithmetic expressions (builds on top of enumerating permutations)
- Review standard functions you might use in Racket: accumulate, map, map-indexed, fold-left, fold-right. Not just how they're implemented and linear-recursive vs linear-iterative, but also Same with `set`s.
- ✯ n queens and dancing links (still want to try it, probably not good for an article)
- Abstract algebra with multiplve variables: Groebner bases, various algos.
- It would be really cool to implement some of Katherine Stange's [Visualizing imaginary quadratic fields](https://math.colorado.edu/~kstange/papers/Stange-short-exp.pdf).


















# Symbols and SICP Library Functions
## Symbols and Special Forms
**Chapter 1.1:**
```rkt
+ - * / 
display newline 
if cond
and or not
```

**Chapter 1.2:** 
```rkt
remainder
display
(runtime)
```

**Chapter 1.3:** 
```rkt
lambda
let
error
```

**Chapter 2.1:** 
```rkt
cons
car, cdr
pair?
```
**Chapter 2.2:** 
```rkt
nil ; More commonly '() or (list)
list
list-ref, length
cadr, caddr
append
map
```


# The ill-fated Santa Barbara Monte Carlo machine

# Exact runtime of count-change
The solution for the number of nodes in the count-change graph 
can be written out exactly. At the very least, we can write a big 
500x500 matrix and write the number of nodes required as a function of $M^n$ 
applied to some vector. Problems like this are kind of fun, so it would be 
nice to just do this, put it in Jordan normal form. We'll end up 
with a fifth degree polynomial, and $T(n,5)=P(n) + \cos(...)$ where the "cos" is a placeholder for a bunch of complicated but finite bounded oscillatory terms.
# RSA implementation
# Linear diophantine equations 
 - The extended GCD algorithm (finding $x,y$ given $a,b$ such that $ax+by=\textrm{gcd}(a,b)$)
 - Chinese remainder theorem algorithm 
 - General linear diophantine equations
# Bonus number theory (Euler totient, base b expansions of fractions)

 - We emphasized the Fibonacci numbers, what about algos for the Lucas numbers?
 - Partition function algorithm
 - Do any cool algorithms arise from the generating functions?
 - Pretty sure there's a catalan number algorithm in plain sight here. 
 - Negative binomial numbers. Maybe do this after the matrix stuff? There's a cool way that the square of an alternating pascal number matrix gives you the identity matrix
```mathematica
alternatingpascal[n_] := 
  Table[Table[If[i <= j, (-1)^i Binomial[j, i], 0], {i, 0, n}], {j, 
    0, n}];
alternatingpascal[10] . alternatingpascal[10] // MatrixForm
```
# Bonus special numbers (Lucas, Catalan, partition numbers, "negative binomial")
# Numerical approximation formulas 
(iterated polynomial gives sine, other iterated special polynomials give special things too)
I think there's a story to tell here starting with...

 - The nested function approximation for sine. (Who came up with this first? Is there an interesting functional equation from the polynomial?) 
 - The nested function approximation for the feigenbaum function ([this writing by Wolfram](https://writings.stephenwolfram.com/2019/07/mitchell-feigenbaum-1944-2019-4-66920160910299067185320382/) and the code used to generate [this image](https://content.wolfram.com/sites/43/2019/07/feigenbaum-function.png) - click on the image in the article to get the code). I think it can be casted in the same form as the polynomial version: iterated function -> scaled up. See also [Simone Conradi's work](https://mathstodon.xyz/@S_Conradi). This is the solution of the Feigenbaum-Cvitanović functional equation.
 - Other nested functions? I think Simone Conradi also posted code involving $f(f(x))=\sin(x)$. Hell, might as well email Conradi and also Cvitanovic while I'm at it.
 - LLMs recommended studying Schroder's equation and the Abel equation, but I don't quite understand this.
# Improving rates of convergence
I went on a tangent during our meeting about rates of convergence, so a few things could be:
 - How fast Newton's method converges (it's great). Accelerated newton
 - Newton's method in multiple variables, maybe?
 - Successive averaging
 - Resummation schemes

# Ramanujan tau function

✯ Challenge 1: try to compute the Ramanujan tau function. This is some memoized code using recursion that supposedly works: [https://claude.ai/chat/374b1219-3cd8-4a9e-87a3-dfddfc1f8896](https://claude.ai/chat/374b1219-3cd8-4a9e-87a3-dfddfc1f8896), but simple mathematica code can generate it too: `CoefficientList[Take[Expand[Product[(1 - x^k)^24, {k, 1, 30}]], 30],x]`

# Continued fraction expansion of pi
 Challenge 2: Continued fraction expansion of pi or 1/pi using exact arithmetic.

# Reversibility and Quantum Computing

# Drawing Church numerals
algorithm to draw church numerals in the style of the "what is PLUS times PLUS"  video.
# Enumerating binary trees and arithmetic expressions
enumerating partitions, enumerating binary trees (rather than just counting), enumerating expressions?
# n queens and dancing links
# Story about polynomial long division + my grandpa










<div>$$\begin{align*}
\end{align*}$$</div>
<div>$$\begin{align*}
\end{align*}$$</div>
<div>$$\begin{align*}
\end{align*}$$</div>
Well, I mentioned something about measuring asymptotics in a lab. The most famous example of this is the 
polymer statistics of the self-avoiding walk: A long polymer in a solution tends to scrunch up, but it is not a 
random walk because the links of a polymer are physical object and can't overlap with each other. Instead it's a self-avoiding
walk. If the self-avoiding walk has $N$ links, then the expected end-to-end distance is $R(N)\sim N^\nu$. For the random walk
$\nu=1/2.$ For the self-avoiding walk, $\nu$ is known as a critical exponent and 
