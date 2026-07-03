<div class="nav">
    <span class="activenav"><a href="../ch1/notes-ch1-3.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch2-2.html">Next →</a></span>
</div>


[HTML Book Chapter 2.1 Link](https://sarabander.github.io/sicp/html/2_002e1.xhtml#g_t2_002e1)

@toc

## Section 2.1


### Introduction

### Meeting 03-30-2025
- Hindley–Milner  style types.
- LISPs implement memory safety during runtime
- Type safety isn't just about  [...]?
- Runtime issue: generalized form of the halting problem; 
- Halting problem: https://en.wikipedia.org/wiki/Rice%27s_theorem and https://en.wikipedia.org/wiki/Rice%E2%80%93Shapiro_theorem -- relevant if we ask what static things we can say about a program (without running it)
- Rust is guaranteed to not have false negatives about memory safety [?]
- Type safety 
- https://nature-of-computation.org/ -- https://en.wikipedia.org/wiki/Christos_Papadimitriou has some interesting has some interesting, approachable books. 
- https://hbpms.blogspot.com/
- https://hackernewsbooks.com/
- https://people.eecs.berkeley.edu/~bh/sicp.html

### Exercises 

#### Exercise 2.1

Define a better version of
`make-rat` that handles both positive and negative arguments.
`Make-rat` should normalize the sign so that if the rational number is
positive, both the numerator and denominator are positive, and if the rational
number is negative, only the numerator is negative.

##### Solution

@src(code/ex2-1.rkt)

#### Exercise 2.2

Consider the problem of
representing line segments in a plane.  Each segment is represented as a pair
of points: a starting point and an ending point.  Define a constructor
`make-segment` and selectors `start-segment` and `end-segment`
that define the representation of segments in terms of points.  Furthermore, a
point can be represented as a pair of numbers: the $x$ coordinate and the
$y$ coordinate.  Accordingly, specify a constructor `make-point` and
selectors `x-point` and `y-point` that define this representation.
Finally, using your selectors and constructors, define a procedure
`midpoint-segment` that takes a line segment as argument and returns its
midpoint (the point whose coordinates are the average of the coordinates of the
endpoints).  To try your procedures, you'll need a way to print points:

```rkt
(define (print-point p)
  (newline)
  (display "(")
  (display (x-point p))
  (display ",")
  (display (y-point p))
  (display ")"))
```

##### Solution

@src(code/ex2-2.rkt)

#### Exercise 2.3

Implement a representation for
rectangles in a plane.  (Hint: You may want to make use of Exercise 2.2.)
In terms of your constructors and selectors, create procedures that compute the
perimeter and the area of a given rectangle.  Now implement a different
representation for rectangles.  Can you design your system with suitable
abstraction barriers, so that the same perimeter and area procedures will work
using either representation?

##### Solution

Super tedious! I guess this is the 1980's version of "implement these getter functions" -.-

I was tempted to implement a programmatic way to switch between rect1 or rect2 based on a flag passed in, but I think that's overengineering the problem.

@src(code/ex2-3.rkt)

#### Exercise 2.4

Here is an alternative procedural
representation of pairs.  For this representation, verify that `(car (cons
x y))` yields `x` for any objects `x` and `y`.

```rkt
(define (cons x y) 
  (lambda (m) (m x y)))

(define (car z) 
  (z (lambda (p q) p)))
```

What is the corresponding definition of `cdr`? (Hint: To verify that this
works, make use of the substitution model of 1.1.5.)

##### Solution

First, let's check how car works:
```rkt
(car (cons x y))
((lambda (m) (m x y)) (lambda (p q) p))
((lambda (p q) p) x y) 
x
```
So the corresponding definition of `cdr` will just have `(lambda (p q) q)` instead.

@src(code/ex2-4.rkt)

#### Exercise 2.5

Show that we can represent pairs of
nonnegative integers using only numbers and arithmetic operations if we
represent the pair $a$ and $b$ as the integer that is the product ${2^a 3^b}$.
Give the corresponding definitions of the procedures `cons`,
`car`, and `cdr`.

##### Solution

@src(code/ex2-5.rkt)
#### Exercise 2.6

In case representing pairs as
procedures wasn't mind-boggling enough, consider that, in a language that can
manipulate procedures, we can get by without numbers (at least insofar as
nonnegative integers are concerned) by implementing 0 and the operation of
adding 1 as

```rkt
(define zero (lambda (f) (lambda (x) x)))

(define (add-1 n)
  (lambda (f) (lambda (x) (f ((n f) x)))))
```

This representation is known as Church numerals, after its inventor,
Alonzo Church, the logician who invented the λ-calculus.

Define `one` and `two` directly (not in terms of `zero` and
`add-1`).  (Hint: Use substitution to evaluate `(add-1 zero)`).  Give
a direct definition of the addition procedure `+` (not in terms of
repeated application of `add-1`).

##### Solution

How topical! The video ["What is PLUS times PLUS?"](https://www.youtube.com/watch?v=RcVA8Nj6HEo) just came out.

**1:**

```rkt
;; (define zero (lambda (f) (lambda (x) x)))
;; (define (add-1 n) (lambda (f) (lambda (x) (f ((n f) x)))))
(add-1 zero)
(lambda (f) (lambda (x) (f (((lambda (g) (lambda (y) y)) f) x))))
(lambda (f) (lambda (x) (f ((lambda (y) y) x))))
(lambda (f) (lambda (x) (f x)))
```

**2:**

```rkt
;; (define one (lambda (f) (lambda (x) (f x))))
;; (define (add-1 n) (lambda (f) (lambda (x) (f ((n f) x)))))
(add-1 one)
(lambda (f) (lambda (x) (f (((lambda (g) (lambda (y) (g y))) f) x))))
(lambda (f) (lambda (x) (f ((lambda (y) (f y)) x))))
(lambda (f) (lambda (x) (f (f x))))
```

**addition:**
```rkt
(define (church-add a b)
    (lambda (f) (lambda (x) ((a f) ((b f) x)))))
```

**Testing:** Yooo it works first try, nice.

To future-me/future-readers: the idea behind `church-add` is to first unwrap `a` and `b` so that they're simple functions that apply `f` some number of times, then apply both to `x`. 

@src(code/ex2-6.rkt)

#### Exercise 2.7

Alyssa's program is incomplete
because she has not specified the implementation of the interval abstraction.
Here is a definition of the interval constructor:

```rkt
(define (make-interval a b) (cons a b))
```

Define selectors `upper-bound` and `lower-bound` to complete the
implementation.

##### Solution
```rkt
(define (make-interval a b) (cons a b))
(define (lower-bound int) (car int))
(define (upper-bound int) (cdr int))
```

#### Exercise 2.8

Using reasoning analogous to
Alyssa's, describe how the difference of two intervals may be computed.  Define
a corresponding subtraction procedure, called `sub-interval`.

##### Solution

Write our two intervals as $A$ and $B$. The lower bound should be
<div>$$\mathrm{inf}_{x\in A, y\in B}(x-y)=A_{\textrm{min}}-B_{\textrm{max}}$$</div>
The upper bound should be
<div>$$\mathrm{sup}_{x\in A, y\in B}(x-y)=A_{\textrm{max}}-B_{\textrm{min}}$$</div>

```rkt
(define (sub-interval A B)
  (make-interval (- (lower-bound A) (upper-bound B)) 
                 (- (upper-bound A) (lower-bound B))))
```

#### Exercise 2.9

The width of an interval
is half of the difference between its upper and lower bounds.  The width is a
measure of the uncertainty of the number specified by the interval.  For some
arithmetic operations the width of the result of combining two intervals is a
function only of the widths of the argument intervals, whereas for others the
width of the combination is not a function of the widths of the argument
intervals.  Show that the width of the sum (or difference) of two intervals is
a function only of the widths of the intervals being added (or subtracted).
Give examples to show that this is not true for multiplication or division.

##### Solution

**Addition:**
<div>$$\begin{align*}
\textrm{Width}_{A+B} &=
\mathrm{sup}_{x\in A, y\in B}(x+y)-\mathrm{inf}_{x\in A, y\in B}(x+y)\\
&=A_{\textrm{max}}+B_{\textrm{max}} - (A_{\textrm{min}}+B_{\textrm{min}})\\
&=\textrm{Width}_A+\textrm{Width}_B
\end{align*}$$</div>

**Subtraction:**
<div>$$\begin{align*}
\textrm{Width}_{A-B} &=
\mathrm{sup}_{x\in A, y\in B}(x-y)-\mathrm{inf}_{x\in A, y\in B}(x-y)\\
&=A_{\textrm{max}}-B_{\textrm{min}} - (A_{\textrm{min}}-B_{\textrm{max}})\\
&=\textrm{Width}_A+\textrm{Width}_B
\end{align*}$$</div>

**Counterexamples:**
@src(code/ex2-9.rkt)

#### Exercise 2.10

Ben Bitdiddle, an expert systems
programmer, looks over Alyssa's shoulder and comments that it is not clear what
it means to divide by an interval that spans zero.  Modify Alyssa's code to
check for this condition and to signal an error if it occurs.

##### Solution

@src(code/ex2-10.rkt)

#### Exercise 2.11

In passing, Ben also cryptically
comments: ``By testing the signs of the endpoints of the intervals, it is
possible to break `mul-interval` into nine cases, only one of which
requires more than two multiplications.''  Rewrite this procedure using Ben's
suggestion.

##### Solution
So, let's see. The goal here is to reduce the number of multiplications down from 4. We have four numbers $x_\ell,x_u,y_\ell,y_u.$ If we go case-by-case whether each number is greater than or equal to zero, we don't have sixteen cases because we also have to enforce $x_\ell\lt x_u$. I guess it's easier to list this out by cases.

- case `1111`: The positive case `1111` is easy:
<div>$$x*y=[x_\ell y_\ell,x_u y_u]$$</div>

- case `1101`: If all numbers are positive except $y_\ell$ (case `1101`) the lower bound is $x_u y_\ell:$ $x*y=[x_u y_\ell,x_u y_u]$

- case `0111`: By symmetry, if all numbers are positive except $x_\ell,$ then $x*y=[x_u y_\ell,x_u y_u]$

Anyways, proceeding in this way we get the list of sixteen cases:

```txt
x_lower>=0? x_upper>=0? y_lower>=0? y_upper>=0? 
1111 - [x_lower*y_lower, x_upper*y_upper]
1110 - disallowed
1101 - [x_upper*y_lower, x_upper*y_upper]
1100 - [x_upper*y_lower, x_lower*y_upper]
1011 - disallowed
1010 - disallowed
1001 - disallowed
1000 - disallowed
0111 - [x_lower*y_upper, x_upper*y_upper]
0110 - disallowed
0101 - [min(x_lower*y_upper, x_upper*y_lower), max(x_lower*y_lower,x_upper*y_upper)]
0100 - [x_upper*y_lower, x_lower*y_lower]
0011 - [x_lower*y_upper, x_upper*y_lower]
0010 - disallowed
0001 - [x_lower*y_upper, x_lower*y_lower]
0000 - [x_upper*y_upper, x_lower*y_lower]
```

@src(code/ex2-11.rkt)

#### Exercise 2.12

Define a constructor
`make-center-percent` that takes a center and a percentage tolerance and
produces the desired interval.  You must also define a selector `percent`
that produces the percentage tolerance for a given interval.  The `center`
selector is the same as the one shown above.

##### Solution
I'm going to opt to keep my tolerances as pure fractions (no multiplication by 100 to get a pure percent). I find it easiest to first write the percent function:

```rkt
(define (center i) (/ (+ (lower-bound i) (upper-bound i)) 2))
(define (width i) (/ (- (upper-bound i) (lower-bound i)) 2))
(define (percent i) (/ (width i) (center i)))
```

Then, `(make-center-percent x p)` should be defined as the interval $i$ with
<div>$$\frac{i_\ell+i_u}{2}=x,\qquad \frac{i_u-i_\ell}{i_u+i_\ell}=p$$</div>
Which has the solution
<div>$$i_\ell=x-px,\qquad i_u=x+px$$</div>
which we should have known but it's nice to write it out in full!
```rkt
(define (make-percent-center x p)
    (make-interval (- x (* x p)) (+ x (* x p))))
```
#### Exercise 2.13

Show that under the assumption of
small percentage tolerances there is a simple formula for the approximate
percentage tolerance of the product of two intervals in terms of the tolerances
of the factors.  You may simplify the problem by assuming that all numbers are
positive.

##### Solution
<div>$$\begin{align*}
(a+\Delta a)(b+\Delta b)&=ab+b\Delta a+a\Delta b+\Delta a\Delta b\\
&\approx ab+b\Delta a+a\Delta b\\
&=ab\left(1+\frac{\Delta a}{a}+\frac{\Delta b}{b}\right)
\end{align*}$$</div>
So the percent tolerances add.

#### Exercise 2.14

Demonstrate that Lem is right.
Investigate the behavior of the system on a variety of arithmetic
expressions. Make some intervals $A$ and $B$, and use them in computing the
expressions $A / A$ and $A / B$.  You will get the most insight by
using intervals whose width is a small percentage of the center value. Examine
the results of the computation in center-percent form (see Exercise 2.12).

##### Solution

@src(code/ex2-14.rkt)

This makes sense, the percent errors add (under the small error approximation).

#### Exercise 2.15

Eva Lu Ator, another user, has
also noticed the different intervals computed by different but algebraically
equivalent expressions. She says that a formula to compute with intervals using
Alyssa's system will produce tighter error bounds if it can be written in such
a form that no variable that represents an uncertain number is repeated.  Thus,
she says, `par2` is a better program for parallel resistances than
`par1`.  Is she right?  Why?

##### Solution
**Alyssa's Conjecture:** Among algebraically equivalent expressions 
the one that minimizes the error of the result interval is the one in which 
no variable that represents an uncertain number is repeated, if such a form exists.

**My statement:** Every operation involving two intervals of width greater than zero adds to the error, so those are the things we want to minimize.

**Question:** is there a expression such that making a variable occur only once adds to the total number of interval operations?

- Polynomials are out. Let's count `(pow A 3)` as the symbol `A` occurring multiple times.
- The only expressions we can form are binary trees, the way to minimize the number of nontrivial interval operations **is** to ensure each symbol only occurs once, if that's possible. If we have 4 variables and 4 nontrivial leaf nodes, we'll have 3 nontrivial interval combinations. (Evaluating nodes of the tree: Every operation takes in two intervals and returns 1, so the number of nontrivial intervals can only decrease by one)
- The question now is, is minimizing the number of nontrivial interval combinations the way to go?!

- "Any operation between two intervals will increase errors" - I can prove this.
- "The binary tree with the smallest number of nontrivial intervals as leaf nodes minimizes the number of nontrivial interval operations." - I can also prove this
- The problem is + and * increase the errors by different amounts, so if I reduce the total number of operations, but introduce a * to the wrong spot, what if this blows up the error? So my concern is really about allowed transformations on the binary tree and the interplay between + and * (or -, or /). For example in this code snippet to evaluate $A/B + C/B,$ we reduce the number of divisions, but don't reduce the error.

@src(code/ex2-15.rkt)

I'm going to leave this problem here. It's probably true, I'm just having trouble proving it.

#### Exercise 2.16

Explain, in general, why
equivalent algebraic expressions may lead to different answers.  Can you devise
an interval-arithmetic package that does not have this shortcoming, or is this
task impossible?  (Warning: This problem is very difficult.)

##### Solution
Consider the context of problem 2.15, where we care about the expression $ab/(a+b)$.

- The gold standard is to model each number as a random variable, possibly with a joint probability distribution $P(a,b)$. Then you ask what is the probability distribution 
$$P\left(\frac{ab}{a+b}\right)=P\left(\frac{1}{\frac{1}{a}+\frac{1}{b}}\right)$$
This can be done through monte carlo, or bootstrap and jackknife, or through linear error propagation, there's a ton of methods.

- Another simpler heuristic would be to treat our expression as a function:
```rkt
;; equivalent definitions
(define (f a b) (/ (* a b) (+ a b)))
(define (f a b) (/ 1 (+ (/ 1 a) (/ 1 b))))
```
and then the new interval would have bounds
```rkt
(let ((al (lower-bound A))
      (au (upper-bound A))
      (bl (lower-bound B))
      (bu (upper-bound B)))
  (let ((x1 (f al bl))
        (x2 (f al bu))
        (x3 (f au bl))
        (x4 (f au bu)))
    (make-interval (min x1 x2 x3 x4)
                   (max x1 x2 x3 x4))))
```
In many cases the result will be the smallest interval possible. But we could have pathological cases with non-monotonic functions (the extreme cases can lie in the middle of the interval instead of the endpoints; so maybe "convex" is the word I'm searching for). 

So anyways this is just a discussion of the possible approaches, we're not going to actually implement all this stuff.














