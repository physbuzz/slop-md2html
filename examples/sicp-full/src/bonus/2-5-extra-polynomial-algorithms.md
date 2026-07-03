# The Abstract Algebra of Chapter 2.5

The system of generic operations discussed in SICP is perfect for starting a 
discussion about abstract algebra, because we've already learned
the mathematical details. So the code can be the foundation. 
Part of this article is explaining the exact same foundation using 
mathematical jargon, and then we can understand the systems and extend it to
other interesting systems.

## The Definition of a Ring

The properties that we saw in our system of generic operations center around
a mathematical object called a ring. In SICP terms, this means that
each of our types are equipped with a `'mul`, `'add`, and `'negate` operation,
such that multiplication and addition "behave as expected." In addition, 
we need an additive identity `(get 'my-type 'zero)` and a multiplicative
identity `(get 'my-type 'one)`. 

Our type `'my-type` is a **ring** if it satisfies the following four 
sets of properties. 

**0.** The operations `'add`, `'mul`, and `'negate` are all closed under
addition. That is, given arguments of type `'my-type`, we return values
of type `'my-type`. In addition, `'zero` and `'one` are elements of type `'my-type`.

**1.** `'my-type` is an abelian group under addition, meaning the following comparisons 
return true for every input `a,b,c` of type `'my-input`.
```scm
;; Addition is commutative
(equal? (add a b) (add b a))
;; Addition is associative
(equal? (add (add a b) c) (add a (add b c)))
;; The zero element, which satisfies a+0 == a
(define zero (get 'my-type 'zero))
(equal? (add a zero) a)
;; Negation, there exists an additive inverse
(equal? (add a (negate a)) zero)
```

**2.** `'my-type` is a monoid under multiplication: 
```scm
;; Multiplication is associative
(equal? (mul (mul a b) c) (mul a (mul b c)))
;; The multiplicative identity, which satisfies a*1 == 1*a == a
(define one (get 'my-type 'one))
(equal? (mul a one) a)
(equal? (mul one a) a)
```

**3.** `'my-type` satisfies the distributive law with respect to addition: 
```scm
;; Left-distributivity
(equal? (mul a (add b c)) (add (mul a b) (mul a c)))
;; Right-distributivity
(equal? (mul (add b c) a) (add (mul b a) (mul c a)))
```

## More Examples of Rings

Great! I'd like to emphasize that this is the full mathematical definition
of a ring. As such it's very general. The examples given in SICP chapter
2.5 are...

 - The integers as `'scheme-number` (presumably). These are denoted
by $\mathbb{Z}$. 
 - The rationals as `'rational`. These are denoted $\mathbb{Q}$. 
 - The complex numbers as `'complex`. These are denoted $\mathbb{C}$. (I am 
completely glossing over the issues of floating point arithmetic here,
which might break some of the equalities above)
 - The polynomials `'polynomial` over any of the above rings. These are 
denoted $\mathbb{Z}[x],$ $\mathbb{Q}[x],$ and $\mathbb{C}[x].$

There are loads of other rings we could define. For example, let's look at 
the integers modulo 12, denoted $\mathbb{Z}_{12}.$ These will have type `'int-mod-12` and multiplication
operation
```rkt
;; inside (install-int-mod-12)
(define (mul a b)
  ((* a b) remainder 12))
```
Clearly then, we have an interesting situation where `(mul 4 3)` will 
return $0$! $4$ and $3$ are called zero divisors, and we often want to work
in a ring without zero divisors. Such a ring without any zero
divisors is known as an *integral domain*, and I italicised that term because
if you're ever going to take an abstract algebra course at a university you
might as well put that on a flashcard and memorize it now!
 

Another example is that of square n-by-n matrices for some given n. Let's say
we define the type `'matrix-2x2`, and we care about matrices with integer 
coefficients. This ring is denoted $M_2(\mathbb{Z}).$ Interestingly, this ring
has zero divisors:

$$\begin{bmatrix} 1 & 0 \\\\ 0 & 0 \end{bmatrix}\begin{bmatrix} 0 & 0 \\\\ 0 & 1 \end{bmatrix} = \begin{bmatrix} 0 & 0 \\\\ 0 & 0 \end{bmatrix}$$

We can also see that this is our first example of a noncommutative ring! We can see this by observing that
$$\begin{bmatrix} 0 & 1 \\\\ 0 & 0 \end{bmatrix}\begin{bmatrix} 0 & 0 \\\\ 1 & 0 \end{bmatrix} = \begin{bmatrix} 1 & 0 \\\\ 0 & 0 \end{bmatrix},$$
while
$$\begin{bmatrix} 0 & 0 \\\\ 1 & 0 \end{bmatrix}\begin{bmatrix} 0 & 1 \\\\ 0 & 0 \end{bmatrix} = \begin{bmatrix} 0 & 0 \\\\ 0 & 1 \end{bmatrix}.$$

You could imagine any of these being problem sets in SICP: create a ring, 
run `(install-ring)`, and demonstrate some of its interesting properties. 

## What properties did we see of polynomials?

Let's go back to the interesting properties of *commutative rings*. That is,
rings where we have the additional property
```rkt
;; Commutativity of multiplication
(equal? (mul a b) (mul b a))
```

Given any ring $R$, we can define the polynomial ring $R[x].$ In fact since our
code was implemented using generics, the multiplication and addition operations
involve no extra effort on our part. The fact that $R[x]$ is a ring follows
from the fact that $R$ is a ring.

### A (sort of?) Interesting Isomorphism

Taking this "building polynomial rings" thing to its annoying conclusion, 
what about $(R[y])[x]$? ie, polynomials
in $x$ with coefficients taken from $R[y]$? In SICP, we were given the example
of the following polynomial:

$$(y^2+1)x^3+(2y)x+1$$

which we might represent as the following data structure:
```rkt
'(polynomial x
  (3 (polynomial y (2 1) (0 1)))
  (1 (polynomial y (1 2)))
  (0 (polynomial y (0 1))))
```

In exercise 2.92, we're asked to redesign the polynomial system to work with
multivariate polynomials natively. 

> **Exercise 2.92:** By imposing an ordering on variables, extend the polynomial package so that addition and multiplication of polynomials works for polynomials in different variables. (This is not easy!)

This is an open-ended question, but in my solution, I would represent the 
polynomial above: 

$$x^3y^2+x^3+2xy+1$$

With the following Lisp representation:

```rkt
'(polynomial-multivariate
  (1 ((x 3) (y 2)))
  (1 ((x 3) (y 0)))
  (2 ((x 1) (y 1)))
  (1 ((x 0) (y 0))))
```

Transforming between these two polynomial representations would be some 
function that we'd have to define, and is an example of an isomorphism:
a one-to-one invertible map that preserves multiplication/addition. 
In mathematics, we'd write:

$$(R[y])[x]\simeq R[x,y]$$

I mean, this isn't that interesting because it's something we intuitively
know. But it's a nice example where we really have to write a 
Lisp function to coerce one type into another, and we end up with a mathematical
isomorphism.

## The property that made me write this article

Integer division: if $|b|\lt |a|$ and we want to compute `(remainder a b)`, 
we subtract off as many copies of `b` as possible until we find an integer 
with smaller absolute value than `b` or we reach zero.

```rkt
(define (remainder a b)
  (cond ((= b 0) (error "division by zero"))
        ((= a 0) 0)
        ((< (abs a) (abs b)) a)
        (else (remainder (- a (* b (* (sgn a) (sgn b)))) b))))
```

Polynomial division: we saw this in exercise 2.91, to get the remainder
we subtract off the monomial with coefficient and order defined by 
the code in the book:
```rkt
  (let ((new-c (div (coeff t1) 
                    (coeff t2)))
        (new-o (- (order t1) 
                  (order t2))))
```
Because we have a division here, we should note that we only defined 
polynomial division for $\mathbb{Q}[x]$! This is actually a deep insight, 
and we cannot perform a simple Euclidean division algorithm over 
$\mathbb{Z}[x].$ In fact, this is what exercise 2.95 shows: with our
default algorithm, we find:
$$\textrm{GCD}\left( (x^2-2x+1)(11x^2+7) , (x^2-2x+1)(13x+5)\right)=\frac{1458}{169}x^2-\frac{2916}{169} x + \frac{1458}{169}$$
we say that "the GCD is only defined up to multiplication by units." In this 
context a unit is an invertible element of the base ring $\mathbb{Q}.$ Because
every element in $\mathbb{Q}$ except zero is invertible, our GCD is only 
defined up to multiplication by rational numbers.

What other rings have a Euclidean algorithm? Such domains are called 
*Euclidean domains.* If you plan on going to grad school for math, 
you might as well put this on a flash card and memorize it now! Well, 
it's probably better to memorize the [wikipedia definition](). 

A Euclidean domain is a commutative ring $R$ with no zero divisors, endowed
with a function $f:R\to \mathbb{Z}^{\ge 0}$ such that, we can perform division
with remainder. eg, for any two elements $a$ and $b$, there exist $q$ and 
$r$ such that $a=bq+r$ and either $r=0$ or $f(r)\lt f(b).$ 

So long as we have such a function, we can always perform the Euclidean
GCD algorithm and, assuming that the elements $q$ and $r$ can be found 
algorithmically, it will always terminate after a finite number of steps! 

Examples of Euclidean domains include...

 - The Gaussian integers $\mathbb{Z}[i],$ that is complex numbers of the form
$\{a+bi : (a,b)\in\mathbb{Z}^2\}.$ This is also known as "the ring of integers of $\mathbb{Q}[\sqrt{-1}].$"
 - The Eisenstein integers $\mathbb{Z}[e^{2\pi i/3}],$ that is complex numbers of the form
$\{a+be^{2\pi i/3} : (a,b)\in\mathbb{Z}^2\}.$ Note that $e^{2\pi i/3}=(-1+\sqrt{-3})/2,$ and so the Eistenstein integers are also "the ring of integers of $\mathbb{Q}[\sqrt{-3}].$"
 - The ring $\mathbb{Z}[\sqrt{2}],$ that is real numbers of the form $\{a+b\sqrt{2} :  (a,b)\in\mathbb{Z}^2\}.$ You guessed it, these are "the ring of integers of $\mathbb{Q}[\sqrt{2}].$"


## The Gaussian integers

### SICP-style package for the Gaussian Integers

gcd algorithm

frequency of coprime numbers



### Gaussian coprime numbers

frequency of coprime numbers

### Finding and plotting Gaussian primes

## The Eisenstein integers

gcd

coprime

# Scratchwork

- We saw how long division works for polynomials
- The example with $P_1,$ $P_2,$ $P_3$ is particularly illustrative.
- In general, a division algorithm works on something called a Euclidean Domain.

From Aluffi's "Algebra: Chapter 0", we have

**Definition 2.7.** A *Euclidean valuation* on an integral domain R is a function $v:R\setminus \{0\}\to \mathbb{Z}^{\ge 0}$ satisfying the following property: for all $a\in R$ and all nonzero $b\in R$ there exist
$q, r \in R$ such that $a = qb + r,$ with either $r = 0$ or $v(r) < v(b)$. An integral domain B is a Euclidean domain if it admits a Euclidean valuation.

So, if we have such a property, then we can always do a GCD algorithm. Each time we apply Euclidean division, we get a remainder $r$ whose valuation is one lower. 

Our Euclidean algorithm is...

```rkt
(define (gcd a b) 
  (if (apply-generic '=zero? b) a
    (gcd b (apply-generic 'remainder a b))))
```
At each step we reduce the valuation of our arguments by one. We may have a $b$ which isn't
zero but with a zero valuation, but this means that on the next step $(remainder a b)$ 
returns an element of the ring which either has lower valuation or which is equal to zero. 
Since it's not possible to have a negative valuation, this must return zero. So this
proves that the Euclidean algorithm terminates after a finite number of steps.

As we saw, things are only defined up to **units**. So we have to define units somewhere here.

Also, define coprime in this context. 

It would be nice to have a factorization algorithm, but this gets quite complicated. Kronecker's method can be mentioned.









https://www.semanticscholar.org/paper/A-Stroll-Through-the-Gaussian-Primes-Gethner-Wagon/7b7eb90bdbc4b37822ff92875870d0fa4d4fcc2a/figure/2
https://www.semanticscholar.org/paper/A-Stroll-Through-the-Gaussian-Primes-Gethner-Wagon/7b7eb90bdbc4b37822ff92875870d0fa4d4fcc2a/figure/4
https://www.mathpuzzle.com/Gaussians.html
http://www.asiapacific-mathnews.com/06/0602/0010_0014.pdf

