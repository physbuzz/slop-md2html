<div class="nav">
    <span class="activenav"><a href="notes-ch1-2.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="inactivenav"><a href="../ch2/notes-ch2-1.html">Next →</a></span>
</div>


[https://sarabander.github.io/sicp/html/1_002e3.xhtml](https://sarabander.github.io/sicp/html/1_002e3.xhtml)

@toc

## Section 1.3

The following are equivalent:
```rkt
(define (plus4 x) (+ x 4))
(define plus4 (lambda (x) (+ x 4)))
```

I find the example extremely instructive:

$$f(x,y)=x(1+xy)^2+y(1-y)+(1+xy)(1-y)$$
We probably want to only calculate $1+xy$ and $1-y$ once. So,
```rkt
(define (f x y)
  (define (f-helper a b)
    (+ (* x (square a))
       (* y b)
       (* a b)))
  (f-helper (+ 1 (* x y)) 
            (- 1 y)))
;; =>
(define (f x y)
  ((lambda (a b)
     (+ (* x (square a)) 
        (* y b) 
        (* a b)))
   (+ 1 (* x y))
   (- 1 y)))
;; =>
(define (f x y)
  (let ((a (+ 1 (* x y)))
        (b (- 1 y)))
    (+ (* x (square a))
       (* y b)
       (* a b))))
```
In short, 
```rkt
(let ((⟨var₁⟩ ⟨exp₁⟩)
      (⟨var₂⟩ ⟨exp₂⟩)
      …
      (⟨varₙ⟩ ⟨expₙ⟩))
  ⟨body⟩)
;; is alternative syntax for
((lambda (⟨var₁⟩ … ⟨varₙ⟩)
   ⟨body⟩)
 ⟨exp₁⟩
 …
 ⟨expₙ⟩)
```

... 1.3.3 just talks about boring stuff: fixed point function, interval search, fixed point with averaging.

... 1.3.4 just defines numerical stuff, `average-damp`, `newtons-method` (using numerical differentiation).

### Meeting 03-23-2025

- `define` creates a symbol in the environment and sets a value
- `lambda` creates an anonymous function.
- [the binding concept on LISP programming language](https://stackoverflow.com/q/40816760)
- They are in fact using closures
- Closure and closure property - Usage of the term in this book might not be the same.
- Remember special forms break the convention to evaluate all the parameters before the left-most term is called! **Can we illustrate this with display?**
- Side note: Meant to say Python Tutor: https://pythontutor.com/ - why's there no lisptutor?
- "it's just a way to call functions in parallel with local variables that don't share the same memory space." - Lexical closures, vs. mathematical closures
- https://sarabander.github.io/sicp/html/3_002e2.xhtml
- https://en.wikipedia.org/wiki/SHRDLU
- https://en.wikipedia.org/wiki/Paradigms_of_AI_Programming
- https://en.wikipedia.org/wiki/Cyc




### Exercises


#### Exercise 1.29
Simpson's Rule is a more accurate
method of numerical integration than the method illustrated above.  Using
Simpson's Rule, the integral of a function $f$ between $a$ and $b$ is
approximated as


$$\frac{h}{3} \left(y_0 + 4y_1 + 2y_2 + 4y_3 + 2y_4 + \ldots + 2y_{n-2} + 4y_{n-1} + y_n\right)$$
where $h = (b - a)/n$, for some even integer $n$, and
$y_k = f(a + kh)$.  (Increasing $n$ increases the
accuracy of the approximation.)  Define a procedure that takes as arguments
$f,$ $a,$ $b,$ and $n$ and returns the value of the integral, computed
using Simpson's Rule.  Use your procedure to integrate `cube` between 0
and 1 (with $n = 100$ and $n = 1000$), and compare the results to those of
the `integral` procedure shown above.

##### Solution

@src(ch1-code/ex1-29.rkt)

A quick google search shows that Simpson's rule is an exact quadrature (it gives exact results for polynomials of degree 3 or less), so this is expected.

NB: the generalization of quadrature rules that give exact results for all polynomials of degree $2n-1$ is given by [Gaussian quadrature](https://en.wikipedia.org/wiki/Gaussian_quadrature).

#### Exercise 1.30
The `sum` procedure above
generates a linear recursion.  The procedure can be rewritten so that the sum
is performed iteratively.  Show how to do this by filling in the missing
expressions in the following definition:

```rkt
(define (sum term a next b)
  (define (iter a result)
    (if ⟨??⟩
        ⟨??⟩
        (iter ⟨??⟩ ⟨??⟩)))
  (iter ⟨??⟩ ⟨??⟩))
```
##### Solution

@src(ch1-code/ex1-30.rkt)

#### important footnote:
> The
> intent of Exercise 1.31 through Exercise 1.33 is to demonstrate the
> expressive power that is attained by using an appropriate abstraction to
> consolidate many seemingly disparate operations.  However, though accumulation
> and filtering are elegant ideas, our hands are somewhat tied in using them at
> this point since we do not yet have data structures to provide suitable means
> of combination for these abstractions.  We will return to these ideas in
> 2.2.3 when we show how to use sequences as interfaces
> for combining filters and accumulators to build even more powerful
> abstractions.  We will see there how these methods really come into their own
> as a powerful and elegant approach to designing programs.

#### Exercise 1.31

1. The `sum` procedure is only the simplest of a vast number of similar
abstractions that can be captured as higher-order procedures.  Write an analogous
procedure called `product` that returns the product of the values of a
function at points over a given range.  Show how to define `factorial` in
terms of `product`.  Also use `product` to compute approximations to
$\pi$ using the formula
$$\frac\pi4 \,=\, \frac{2\cdot 4\cdot 4\cdot 6\cdot 6\cdot 8\cdot\cdots}{3\cdot 3\cdot 5\cdot 5\cdot 7\cdot 7\cdot\cdots}.$$

2. If your `product` procedure generates a recursive process, write one that
generates an iterative process.  If it generates an iterative process, write
one that generates a recursive process.

##### Solution
@src(ch1-code/ex1-31.rkt)

#### Exercise 1.32

**1.** Show that `sum` and `product` (Exercise 1.31) are both special
cases of a still more general notion called `accumulate` that combines a
collection of terms, using some general accumulation function:
```rkt
(accumulate 
 combiner null-value term a next b)
```
`Accumulate` takes as arguments the same term and range specifications as
`sum` and `product`, together with a `combiner` procedure (of
two arguments) that specifies how the current term is to be combined with the
accumulation of the preceding terms and a `null-value` that specifies what
base value to use when the terms run out.  Write `accumulate` and show how
`sum` and `product` can both be defined as simple calls to
`accumulate`.

**2.** If your `accumulate` procedure generates a recursive process, write one
that generates an iterative process.  If it generates an iterative process,
write one that generates a recursive process.

##### Solution
@src(ch1-code/ex1-32.rkt)

#### Exercise 1.33
You can obtain an even more
general version of `accumulate` (Exercise 1.32) by introducing the
notion of a filter on the terms to be combined.  That is, combine
only those terms derived from values in the range that satisfy a specified
condition.  The resulting `filtered-accumulate` abstraction takes the same
arguments as accumulate, together with an additional predicate of one argument
that specifies the filter.  Write `filtered-accumulate` as a procedure.
Show how to express the following using `filtered-accumulate`:

1. the sum of the squares of the prime numbers in the interval $a$ to $b$
(assuming that you have a `prime?` predicate already written)

2. the product of all the positive integers less than $n$ that are relatively
prime to $n$ (i.e., all positive integers $i \lt n$ such that
$\textrm{GCD}(i, n) = 1$).

##### Solution



@src(ch1-code/ex1-33.rkt)
1. [https://oeis.org/A081738](https://oeis.org/A081738)
2. [https://oeis.org/A001783](https://oeis.org/A001783)

#### Exercise 1.34
Suppose we define the procedure

```rkt
(define (f g) (g 2))
```

Then we have

```rkt
(f square)
4
```

```rkt
(f (lambda (z) (* z (+ z 1))))
6
```

What happens if we (perversely) ask the interpreter to evaluate the combination
`(f f)`?  Explain.

##### Solution

We'll end up calling `(f 2)` which calls `(2 2)`, which should be a syntax error.

@src(ch1-code/ex1-34.rkt)

#### Exercise 1.35 
Show that the golden ratio
$\varphi$ (1.2.2) is a fixed point of the transformation 
$x \mapsto 1 + 1 / x,$ and use this fact to compute $\varphi$ by means 
of the `fixed-point` procedure.

##### Solution

$\varphi$ is defined as the value such that $x=1+1/x,$ which is the definition of a fixed point. What matters more is if it's an attractive fixed point, 
which happens whenever $|f'(x)|\lt 1.$ Since $f'(x)=-1/x^2$ and $\varphi\gt 1,$ $\varphi$ is an attractive fixed point.

@src(ch1-code/ex1-35.rkt)

#### Exercise 1.36
 Modify `fixed-point` so that
it prints the sequence of approximations it generates, using the `newline`
and `display` primitives shown in Exercise 1.22.  Then find a
solution to $x^x = 1000$ by finding a fixed point of $x \mapsto
{\log(1000) / \log(x)}$.  (Use Scheme's primitive `log`
procedure, which computes natural logarithms.)  Compare the number of steps
this takes with and without average damping.  (Note that you cannot start
`fixed-point` with a guess of 1, as this would cause division by
$\log(1) = 0$.)

##### Solution

Without averaging, getting 1 part in $10^4$ accuracy takes 30 function evaluations (starting at 1.5). With averaging, 9 steps.

@src(ch1-code/ex1-36.rkt)

I was confused on the let syntax; inside `(define (try ...) ...)` these two are equivalent:

```rkt
 (define (try guess)
   (let ((next (f guess)))
     (if (close-enough? guess next)
         next
         (try next))))
 (define (try guess)
   ((lambda (next) 
      (if (close-enough? guess next)
      next
      (try next)))
    (f guess)))
```

#### Exercise 1.37

**1.** An infinite continued fraction is an expression of the form
$$f \,=\, {\frac{N_1}{D_1 + \frac{N_2}{D_2 + \frac{N_3}{D_3 + \dots}}}.}$$
As an example, one can show that the infinite continued fraction expansion with
the $N_i$ and the $D_i$ all equal to 1 produces $1 / \varphi$, where
$\varphi$ is the golden ratio (described in 1.2.2).  One way to
approximate an infinite continued fraction is to truncate the expansion after a
given number of terms.  Such a truncation--a so-called k-term
finite continued fraction--has the form
$${\frac{N_1}{D_1 + \frac{N_2}{\ddots + \frac{N_k}{D_k}}}.}$$
Suppose that `n` and `d` are procedures of one argument (the term
index $i$) that return the $N_i$ and $D_i$ of the terms of the
continued fraction.  Define a procedure `cont-frac` such that evaluating
`(cont-frac n d k)` computes the value of the $k$-term finite continued
fraction.  Check your procedure by approximating $1 / \varphi$ using
```rkt
(cont-frac (lambda (i) 1.0)
           (lambda (i) 1.0)
           k)
```
for successive values of `k`.  How large must you make `k` in order
to get an approximation that is accurate to 4 decimal places?

**2.** If your `cont-frac` procedure generates a recursive process, write one
that generates an iterative process.  If it generates an iterative process,
write one that generates a recursive process.

##### Solution

I find that building the continued fraction from the deepest nesting outwards leads naturally to an iterative algorithm, and going from the top level to the deepest nesting naturally leads to a linear iterative recursive algorithm.

I get that we need 11 levels (so that the deepest calls are to `(d 11)` and `(n 11)`) in order to get four digits of accuracy, however [Solving SICP](https://gitlab.com/Lockywolf/chibi-sicp/-/blob/master/index.pdf?ref_type=heads) gets that we need 14 layers, they're probably just not being as precise.

@src(ch1-code/ex1-37.rkt)

#### Exercise 1.38
 In 1737, the Swiss mathematician
Leonhard Euler published a memoir De Fractionibus Continuis, which
included a continued fraction expansion for $e - 2$, where $e$ is the base
of the natural logarithms.  In this fraction, the $N_i$ are all 1, and
the $D_i$ are successively:

 `1, 2, 1, 1, 4, 1, 1, 6, 1, 1, 8, ...`

Write a program that uses your `cont-frac` procedure from Exercise 1.37 
to approximate $e$, based on Euler's expansion.

##### Solution

@src(ch1-code/ex1-38.rkt)
#### Exercise 1.39
 A continued fraction
representation of the tangent function was published in 1770 by the German
mathematician J.H. Lambert:
$${\tan x} \,=\, {\frac{x}{1 - \frac{x^2}{3 - \frac{x^2}{5 - \dots}}}\,,}$$
where $x$ is in radians.  Define a procedure `(tan-cf x k)` that
computes an approximation to the tangent function based on Lambert's formula.
`k` specifies the number of terms to compute, as in Exercise 1.37.

##### Solution
6 terms gives us a very accurate result for a range of angle arguments:

@src(ch1-code/ex1-39.rkt)

#### Exercise 1.40
Define a procedure `cubic`
that can be used together with the `newtons-method` procedure in
expressions of the form
```rkt
(newtons-method (cubic a b c) 1)
```
to approximate zeros of the cubic $x^3 + ax^2 + bx + c$.

##### Solution

@src(ch1-code/ex1-40.rkt)

#### Exercise 1.41
 Define a procedure `double`
that takes a procedure of one argument as argument and returns a procedure that
applies the original procedure twice.  For example, if `inc` is a
procedure that adds 1 to its argument, then `(double inc)` should be a
procedure that adds 2.  What value is returned by

```rkt
(((double (double double)) inc) 5)
```

##### Solution

@src(ch1-code/ex1-41.rkt)

We see that the expression in question causes sixteen function applications (so it prints out 21). Evaluating step by step:

```rkt
(double double) is (lambda (x) (double (double x)))
(double (lambda (x) (double (double x))))
(lambda (y) ((lambda (x) (double (double x))) ((lambda (x) (double (double x))) y))) which is
(lambda (y) ((lambda (x) (double (double x))) (double (double y)))) which is
(lambda (y) (double (double (double (double y)))))
```
Which leads to $16=2^4$ function applications. Easy.

#### Exercise 1.42
Let $f$ and $g$ be two
one-argument functions.  The composition $f$ after $g$ is defined
to be the function $x \mapsto f(g(x))$.  Define a procedure
`compose` that implements composition.  For example, if `inc` is a
procedure that adds 1 to its argument,

```rkt
((compose square inc) 6)
49
```

##### Solution
@src(ch1-code/ex1-42.rkt)

#### Exercise 1.43
 If $f$ is a numerical function
and $n$ is a positive integer, then we can form the $n^{\text{th}}$ repeated
application of $f$, which is defined to be the function whose value at $x$
is $f(f(\dots (f(x))\dots ))$.  For example, if $f$ is the
function $x \mapsto x + 1$, then the $n^{\text{th}}$ repeated application of $f$ is
the function $x \mapsto x + n$.  If $f$ is the operation of squaring a
number, then the $n^{\text{th}}$ repeated application of $f$ is the function that
raises its argument to the $2^n\text{-th}$ power.  Write a procedure that takes as
inputs a procedure that computes $f$ and a positive integer $n$ and returns
the procedure that computes the $n^{\text{th}}$ repeated application of $f$.  Your
procedure should be able to be used as follows:

```rkt
((repeated square 2) 5)
625
```

Hint: You may find it convenient to use `compose` from Exercise 1.42.

##### Solution
@src(ch1-code/ex1-43.rkt)

#### Exercise 1.44
 The idea of smoothing a
function is an important concept in signal processing.  If $f$ is a function
and $dx$ is some small number, then the smoothed version of $f$ is the
function whose value at a point $x$ is the average of $f(x - dx)$, 
$f(x)$, and $f(x + dx)$.  Write a procedure
`smooth` that takes as input a procedure that computes $f$ and returns a
procedure that computes the smoothed $f$.  It is sometimes valuable to
repeatedly smooth a function (that is, smooth the smoothed function, and so on)
to obtain the n-fold smoothed function.  Show how to generate
the n-fold smoothed function of any given function using `smooth` and
`repeated` from Exercise 1.43.

##### Solution

@src(ch1-code/ex1-44.rkt)

As an example, I smooth the $|x|$ function. As we round off the jagged point at x=0, the evaluation of smoothed abs rises. 
If we evaluate smoothed abs far away from zero, its value won't change.

#### Exercise 1.45
 We saw in 1.3.3
that attempting to compute square roots by naively finding a fixed point of
$y \mapsto x / y$ does not converge, and that this can be fixed by average
damping.  The same method works for finding cube roots as fixed points of the
average-damped $y \mapsto x / y^2$.  Unfortunately, the process does not
work for fourth roots---a single average damp is not enough to make a
fixed-point search for $y \mapsto x / y^3$ converge.  On the other hand, if
we average damp twice (i.e., use the average damp of the average damp of 
$y \mapsto x / y^3$) the fixed-point search does converge.  Do some experiments
to determine how many average damps are required to compute $n^{\text{th}}$ roots as a
fixed-point search based upon repeated average damping of 
$y \mapsto x / y^{n-1}.$  
Use this to implement a simple procedure for computing
$n^{\text{th}}$ roots using `fixed-point`, `average-damp`, and the
`repeated` procedure of Exercise 1.43.  Assume that any arithmetic
operations you need are available as primitives.

##### Solution

I admit I skipped the experimentation step. I conjecture that we need $\left\lfloor \frac{n}{2} \right\rfloor$ average-damps. I haven't tested if we need less than this, but this appears to work.

@src(ch1-code/ex1-45.rkt)

Compare to the exact values:
```
1.414213562373095048...
1.259921049894873164...
1.189207115002721066...
1.148698354997035006...
1.122462048309372981...
1.104089513673812337...
1.090507732665257659...
```
#### Exercise 1.46
Several of the numerical methods
described in this chapter are instances of an extremely general computational
strategy known as iterative improvement.  Iterative improvement says
that, to compute something, we start with an initial guess for the answer, test
if the guess is good enough, and otherwise improve the guess and continue the
process using the improved guess as the new guess.  Write a procedure
`iterative-improve` that takes two procedures as arguments: a method for
telling whether a guess is good enough and a method for improving a guess.
`Iterative-improve` should return as its value a procedure that takes a
guess as argument and keeps improving the guess until it is good enough.
Rewrite the `sqrt` procedure of 1.1.7 and the
`fixed-point` procedure of 1.3.3 in terms of
`iterative-improve`.

##### Solution


@src(ch1-code/ex1-46.rkt)

One interesting thought: `iterative-improve` feels to me like it's very poorly written. It works, but a well-written lightning-fast implementation would exploit tail recursion. 
Is there a tail recursion optimization here? I'm wondering if tail recursion is trivial here.

I don't think that our evaluation model is advanced enough to answer that question. I'm also too lazy to check by timing this code. 
