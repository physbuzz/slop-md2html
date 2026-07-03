<div class="nav">
    <span class="activenav"><a href="../ch2/notes-ch2-5.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch3-2.html">Next →</a></span>
</div>


[HTML Book Chapter 3.1 Link](https://sarabander.github.io/sicp/html/3_002e1.xhtml#g_t3_002e1)

@toc

## Section 3.1

### Notes

- Worth reading: https://gwern.net/doc/math/1975-chaitin.pdf 
- Note on evaluation order: we can use `let*` to evaluate
the arguments of let in order.

Here's some useful code about the equality of different functions in the context of the end of 3.1

@src(code/test.rkt)

### Meeting 05-11-2025

- Relating to the "order of updates", I recently stumbled across an interesting post by Dan Piponi about changing the order of updates of an iterative
algorithm and looking at the result. [mathoverflow post](https://mathoverflow.net/questions/492197/what-is-this-modified-arithmetico-geometric-mean-function), [mathstodon.xyz post](https://mathstodon.xyz/@dpiponi/114468239096746615).

- [Referential transparency](https://en.wikipedia.org/wiki/Side_effect_%28computer_science%29#Referential_transparency) : "Absence of side effects is a necessary, but not sufficient, condition for referential transparency. Referential transparency means that an expression (such as a function call) can be replaced with its value. This requires that the expression is pure, that is to say the expression must be deterministic (always give the same value for the same input) and side-effect free."

Resources on writing a Lisp interpreter:

- [https://craftinginterpreters.com/](https://craftinginterpreters.com/)
- [https://norvig.com/lispy.html](https://norvig.com/lispy.html)
- [https://buildyourownlisp.com/](https://buildyourownlisp.com/)

Not related to this chapter, but I forgot about it until now:

 - [Functional composition w/ Chris Ford](https://www.youtube.com/watch?v=jyNqHsN3pEc)

### Exercises

#### Exercise 3.1

An accumulator is a
procedure that is called repeatedly with a single numeric argument and
accumulates its arguments into a sum.  Each time it is called, it returns the
currently accumulated sum.  Write a procedure `make-accumulator` that
generates accumulators, each maintaining an independent sum.  The input to
`make-accumulator` should specify the initial value of the sum; for
example

```rkt
(define A (make-accumulator 5))

(A 10)
15

(A 10)
25
```

##### Solution

@src(code/ex3-1.rkt)

#### Exercise 3.2

In software-testing applications,
it is useful to be able to count the number of times a given procedure is
called during the course of a computation.  Write a procedure
`make-monitored` that takes as input a procedure, `f`, that itself
takes one input.  The result returned by `make-monitored` is a third
procedure, say `mf`, that keeps track of the number of times it has been
called by maintaining an internal counter.  If the input to `mf` is the
special symbol `how-many-calls?`, then `mf` returns the value of the
counter.  If the input is the special symbol `reset-count`, then `mf`
resets the counter to zero.  For any other input, `mf` returns the result
of calling `f` on that input and increments the counter.  For instance, we
could make a monitored version of the `sqrt` procedure:

```rkt
(define s (make-monitored sqrt))

(s 100)
10

(s 'how-many-calls?)
1
```

##### Solution



@src(code/ex3-2.rkt)


#### Exercise 3.3

Modify the `make-account`
procedure so that it creates password-protected accounts.  That is,
`make-account` should take a symbol as an additional argument, as in

```rkt
(define acc 
  (make-account 100 'secret-password))
```

The resulting account object should process a request only if it is accompanied
by the password with which the account was created, and should otherwise return
a complaint:

```rkt
((acc 'secret-password 'withdraw) 40)
60

((acc 'some-other-password 'deposit) 50)
"Incorrect password"
```

##### Solution

@src(code/ex3-3.rkt)
#### Exercise 3.4

Modify the `make-account`
procedure of Exercise 3.3 by adding another local state variable so that,
if an account is accessed more than seven consecutive times with an incorrect
password, it invokes the procedure `call-the-cops`.

##### Solution

I structured this answer in a bit of a weird way, I want the 
"cops called" message to display when the function
is returned. Not when the returned function is called by the 
user.

@src(code/ex3-4.rkt)

#### Exercise 3.5

Monte Carlo integration
is a method of estimating definite integrals by means of Monte Carlo
simulation.  Consider computing the area of a region of space described by a
predicate $P(x, y)$ that is true for points $(x, y)$ in the
region and false for points not in the region.  For example, the region
contained within a circle of radius 3 centered at (5, 7) is described by the
predicate that tests whether ${(x - 5)^2 + {(y - 7)^2 \le 3^2}}$.  To estimate
the area of the region described by such a predicate, begin by choosing a
rectangle that contains the region.  For example, a rectangle with diagonally
opposite corners at (2, 4) and (8, 10) contains the circle above.  The desired
integral is the area of that portion of the rectangle that lies in the region.
We can estimate the integral by picking, at random, points $(x, y)$ that
lie in the rectangle, and testing $P(x, y)$ for each point to
determine whether the point lies in the region.  If we try this with many
points, then the fraction of points that fall in the region should give an
estimate of the proportion of the rectangle that lies in the region.  Hence,
multiplying this fraction by the area of the entire rectangle should produce an
estimate of the integral.

Implement Monte Carlo integration as a procedure `estimate-integral` that
takes as arguments a predicate `P`, upper and lower bounds `x1`,
`x2`, `y1`, and `y2` for the rectangle, and the number of trials
to perform in order to produce the estimate.  Your procedure should use the
same `monte-carlo` procedure that was used above to estimate $\pi$.
Use your `estimate-integral` to produce an estimate of $\pi$ by
measuring the area of a unit circle.

You will find it useful to have a procedure that returns a number chosen at
random from a given range.  The following `random-in-range` procedure
implements this in terms of the `random` procedure used in 
1.2.6, which returns a nonnegative number less than its
input.

```rkt
(define (random-in-range low high)
  (let ((range (- high low)))
    (+ low (random range))))
```

##### Solution

@src(code/ex3-5.rkt)

#### Exercise 3.6

It is useful to be able to reset a
random-number generator to produce a sequence starting from a given value.
Design a new `rand` procedure that is called with an argument that is
either the symbol `generate` or the symbol `reset` and behaves as
follows: `(rand 'generate)` produces a new random number; `((rand
'reset) ⟨new-value⟩)` resets the internal state variable to the
designated `⟨new-value⟩`.  Thus, by resetting the state, one can generate
repeatable sequences.  These are very handy to have when testing and debugging
programs that use random numbers.

##### Solution

@src(code/ex3-6.rkt)

#### Exercise 3.7

Consider the bank account objects
created by `make-account`, with the password modification described in
Exercise 3.3.  Suppose that our banking system requires the ability to
make joint accounts.  Define a procedure `make-joint` that accomplishes
this.  `Make-joint` should take three arguments.  The first is a
password-protected account.  The second argument must match the password with
which the account was defined in order for the `make-joint` operation to
proceed.  The third argument is a new password.  `Make-joint` is to create
an additional access to the original account using the new password.  For
example, if `peter-acc` is a bank account with password
`open-sesame`, then

```rkt
(define paul-acc
  (make-joint peter-acc 
              'open-sesame 
              'rosebud))
```


will allow one to make transactions on `peter-acc` using the name
`paul-acc` and the password `rosebud`.  You may wish to modify your
solution to Exercise 3.3 to accommodate this new feature.

##### Solution

@src(code/ex3-7.rkt)

#### Exercise 3.8

When we defined the evaluation
model in 1.1.3, we said that the first step in evaluating an
expression is to evaluate its subexpressions.  But we never specified the order
in which the subexpressions should be evaluated (e.g., left to right or right
to left).  When we introduce assignment, the order in which the arguments to a
procedure are evaluated can make a difference to the result.  Define a simple
procedure `f` such that evaluating 

```rkt
(+ (f 0) (f 1))
```


will return 0 if
the arguments to `+` are evaluated from left to right but will return 1 if
the arguments are evaluated from right to left.

##### Solution

@src(code/ex3-8.rkt)
