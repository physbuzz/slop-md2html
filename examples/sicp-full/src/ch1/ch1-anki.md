
# Chapter 1.1
## Question
### Statement
What does Lisp stand for? REPL? What are prefix/postfix/infix? What is a "combination" in Lisp?

### Answer

Lisp = "List Processing". REPL = Read-Eval-Print-Loop. Prefix = `(+ a b)`. Postfix might look something like `(a b +)`. Infix would be `(a + b)`. A combination is term in parentheses of the form `(a b c ...)` where `a` is the operator and `b c ...` are the operands.

## Question
### Statement
How do you define a named constant in Lisp? A named function?
### Answer
Named variable: `(define pi 3.14159)`

Named function: `(define (square x) (* x x))`

## Question
### Statement
Exercise 1.5: how does this procedure evaluate using normal order? Using applicative order?
```rkt
(define (p) (p))
(define (test x y) 
  (if (= x 0) 0 y))
(test 0 (p))
```
### Answer
This is a point of confusion! Using applicative order, we first evaluate the arguments of `test`. One of these is a recursive bomb, so it gets implement recursion right away. This is how Scheme evaluates things, so this program will blow up.

In normal order evaluation, we don't evaluate the arguments right away, and in fact `if` is a special form with an evaluation rule such that in applicative or normal order the unused argument is not evaluated if it doesn't need to be. So `(if (= 0 0) 0 (p))` never evaluates `(p)`. The argument isn't 100% convincing to me, but the bottom line is that Haskell uses normal order evaluation and in Haskell the analogue of `test 0 p` runs just fine, with `p` never evaluating its infinite recursive call.

## Question
### Statement
Loosely define the substitution model of evaluation of a Scheme program, and write out the evaluation of `(f 5)` in the program below using the substitution model.
```rkt
(define (square x) (* x x))
(define (sum-of-squares x y)
  (+ (square x) (square y)))
(define (f a)
  (sum-of-squares (+ a 1) (* a 2)))
(f 5)
```
### Answer
The substitution model is just obtained by evaluating function arguments (applicative order) and then substituting the definitions of thesub-expressions that can be evaluated. 

```rkt
(f 5)
(sum-of-squares (+ 5 1) (* 5 2))
(sum-of-squares 6 10)
(+ (square 6) (square 10))
(+ (* 6 6) (* 10 10))
(+ 36 100)
136
```

## Question
### Statement
How do you write `if` and `cond` statements in Scheme? What's special about their evaluation?
### Answer
`(if bool a b)` is a *special form* which evaluates `bool` and then evaluates `a` if bool is true or `b` if bool is false. 
This breaks the strict rule of applicative order evaluation, which might lead you to believe that `bool a b` are all evaluated.

`cond` is another way to achieve conditional evaluation. Here we see how to evaluate `e1`, `e2`, or `e3` based on Boolean predicates `p1` and `p2`. If p1 is true, then p2, e2, e3 are never evaluated.
```rkt
(cond (p1 e1)
    (p2 e2)
    (else e3))
```

# Chapter 1.2

## Question
### Statement
Write out the linear recursive and linear iterative factorial functions.

### Answer

Linear recursive:
```rkt
(define (factorial n)
  (if (= n 1) 
      1 
      (* n (factorial (- n 1)))))
```
This is "linear recursive" because the size of the "call stack" grows linearly.

Linear iterative:
```rkt
(define (factorial n) 
  (fact-iter 1 1 n))

(define (fact-iter product counter max-count)
  (if (> counter max-count)
      product
      (fact-iter (* counter product)
                 (+ counter 1)
                 max-count)))
```
This is not linear recursive, but it is linear iterative, and it is an example of tail-recursion.

## Question
### Statement
Write out the tree recursive and linear iterative Fibonacci functions.
### Answer
Tree recursive:
```rkt
(define (fib n)
  (cond ((= n 0) 0)
        ((= n 1) 1)
        (else (+ (fib (- n 1))
                 (fib (- n 2))))))
```
Linear iterative:
```rkt
(define (fib n) 
  (fib-iter 1 0 n))

(define (fib-iter a b count)
  (if (= count 0)
      b
      (fib-iter (+ a b) a (- count 1))))
```

## Question
### Statement
What does the statement mean that $f(n)$ is $\Theta(g(n))$?

What about $f(n)=O(g(n))$? $f(n)=\Omega(g(n))$?

### Answer
Technically we must write "As $n\to \infty$" but this is usually omitted.
It means that there exists constants <span>$c_1,c_2$</span> such that for some $N$ and all $n\gt N,$ 

$$c_1 g(n)\leq f(n)\leq c_2 g(n).$$

The other two notations aren't used in SICP. big O is an upper bound $f(n)\leq c_2 g(n),$ big Omega is a lower bound $c_1 g(n)\leq f(n).$ So big Theta is a both lower and upper bound.

## Question
### Statement
What are the $\Theta(n)$ time and space requirements for the linear recursive factorial algorithm? For the linear iterative factorial algorithm?
### Answer
The linear recursive version is $\Theta(n)$ time and space.

The linear iterative version is $\Theta(n)$ time and $\Theta(1)$ space.
## Question
### Statement
What are the $\Theta(n)$ time and space requirements for the linear recursive Fibonacci algorithm? For the tree recursive version?
### Answer
The linear iterative version is $\Theta(n)$ time and $\Theta(1)$ space.

The tree-recursive Fibonacci algorithm takes $\Theta(\varphi^n)$ steps and $\Theta(n)$ space.
## Question
### Statement
Write the recursive `fast-expt` algorithm to compute $b^n$ in $\Theta(\log(n))$ steps.
### Answer
We use the statements $b^n=(b^{n/2})^2$ if $n$ is even and $b^n=b b^{n-1}$ if $b$ is odd.
```rkt
(define (fast-expt b n)
  (cond ((= n 0) 
         1)
        ((even? n) 
         (square (fast-expt b (/ n 2))))
        (else 
         (* b (fast-expt b (- n 1))))))
```
## Question
### Statement
Write the iterative (tail-recursive) `fast-exp` algorithm to compute $b^n$ in $\Theta(\log(n))$ steps.
### Answer
We use the statements $b^n=(b^{n/2})^2$ if $n$ is even and $b^n=b b^{n-1}$ if $b$ is odd.
If $a$ is the return value, we use the statements $ab^n=a (b^2)^{n/2}$ if $n$ is even (do nothing to the return value,
square the base) or $a b^n=(ab)^{n-1}$ if $n$ is odd (map $a\mapsto ab,$ $n\mapsto n-1$, do nothing to base).
```rkt
(define (fast-expt b n)
  (define (fast-expt-iter a b n)
    (cond ((= n 0) a)
          ((= (remainder n 2) 0) (fast-expt-iter a (* b b) (/ n 2)))
          (else (fast-expt-iter (* a b) b (- n 1)))))
  (fast-expt-iter 1 b n))
```
## Question
### Statement
Write the `gcd` algorithm.
### Answer
The relevant theorem for calculating $\textrm{gcd}(a,b)$ is that if $c|a$ and $c|b$, then $c|a-kb$ and $c|b-ka$ for all $k$. 
The most reasonable $k$ to choose would be one that eg. leaves $a-kb\in [0,b).$ This is precisely $a\textrm{ mod }b$.
Whether we do this or $b\textrm{ mod }a$ doesn't change the common divisor, so we should do both until we can't any more.

```rkt
(define (gcd a b)
  (if (= b 0)
    a
    (gcd b (remainder a b))))
```


(*Note:* "$a|b$" means "a divides b." ie, there's some integer $c$ with $ac=b.$)
## Question
### Statement
Outline the `prime?` and `fast-prime?` algorithms.
### Answer
In the simple SICP implementation of `prime?`, we create a function `smallest-divisor` which 
iteratively checks the numbers 2 through $n$ to see if they divide $n$. If the smallest divisor
of $n$ is $n,$ then it's prime.

In the `fast-prime?` algorithm, we check if $a^{n-1}\equiv 1\textrm{ mod }n$ for several random $a.$ 
For a prime (or a Carmichael number!) this holds true for all $a.$ If the test fails we've proved that $n$ is non-prime.
If the test passes everything we throw at it, then $n$ is prime or a carmichael number, but carmichael numbers are rare. 
More advanced arguments are needed to ask how many $a$ we need to test, but it's not many.
## Question
### Statement
What's Fermat's little theorem?
### Answer
Fermat's little theorem is that $a^p\equiv a\textrm{ mod }p$ for prime $p.$ 

It can be restated as saying that <span>$\mathbb{Z}_p^{\times}$</span> is a 
cyclic group of order $p-1$ generated by any one of its elements.
## Question
### Statement
What's the Chinese remainder theorem?
### Answer
It's the statement that if <span>$a_1,\ldots,a_k$</span> are any integers and <span>$n_1,\ldots,n_k$</span>
are pairwise coprime, then the system of equations
<span>$x\equiv a_i\textrm{ mod }n_i$</span> has a solution for $x$, and that any two solutions 
are congruent modulo <span>$N=n_1\cdot n_2\cdots n_k.$</span>

Group theoretically, it defines a ring isomorphism 

<div>$$\mathbb{Z}_{n_1\cdot n_2\cdots n_k}\simeq \mathbb{Z}_{n_1}\times\cdots\times\mathbb{Z}_{n_k}$$</div>

# Chapter 1.3
## Question
### Statement
What are the two equivalent ways to define a function, one with a lambda and one without?
### Answer
We can do things the following two ways:
```rkt
(define (func argument) (function definition))
(define func (lambda (argument) (function definition)))
```
## Question
### Statement
What are the use cases for the `let` keyword? How do you use `let` with only one variable (get the parentheses right)?
### Answer
Let is useful for defining local variables with helpful names. It's also useful for making sure that a local variable is only evaluated once and then substituted multiple places, rather than being evaluated multiple times. 

While it's equivalent to a lambda, in the corresponding lambda expression the variable definitions come after the function body, whereas for readability it's better if the variable definitions come before the function body.
## Question
### Statement
What is the definition of `let` in terms of lambdas?
### Answer
```rkt
;; This let
(let ((v1 arg1) (v2 arg2)) (function-body))
;; is equivalent to:
((lambda (v1 v2) (function-body)) arg1 arg2)
```
## Question
### Statement
Give an example of a closure in a returned function (in the broad functional programming sense, not the sense used in SICP).
### Answer
Here we return a function which multiplies by the desired value:

```rkt
(define (multiply-by n) (lambda (m) (* n m)))
```

# Chapter 2.1
## Question
### Statement
What does `cons` do? How do you access the elements of a `cons`?
How do you check if something is an object created by `cons`?
### Answer
`(cons x y)` constructs a pair. To get the first element `x` we do `(car z)`,
to get the second element we do `(cdr z)`.

To check if something is a pair, use the special form `pair?`

## Question
### Statement
What do the functions `cadr` and `caddr` do?
### Answer
`(cadr x)` does `(car (cdr x))`. `(caddr x)` does `(car (cdr (cdr x)))`.

## Question
### Statement
What are the Church numeral definitions of `zero` and `add-one`?
### Answer
The idea is that they're pure lambdas. Zero, given a function and an $x$ returns $x$. $n$ applies $f$ $n$ times. 
So `(zero f)` is the identity function. `(two f)` is `(lambda (x) (f (f x)))` and so on.

```rkt
(define zero (lambda (f) (lambda (x) x)))
(define (add-1 n)
  (lambda (f) (lambda (x) (f ((n f) x)))))
```
# Chapter 2.2
## Question
### Statement
What is the definition of a sequence in terms of `cons` and `nil`? How do you construct a sequence? In Scheme?
### Answer
`(list 1 2 3)` is equivalent to `(cons 1 (cons 2 (cons 3 nil)))`.

You can construct a sequence with the list keyword.

This is also usually just written `'(1 2 3)`. "nil" is an SICP-ism and can also be written as `'()`. 
## Question
### Statement
How do we write an empty sequence? How do we test for an empty sequence?
### Answer
An empty sequence is `nil`, or `(list)`, or `'()`.

We test for an empty sequence using the built-in `null?`
## Question
### Statement
How do we find the first, second, third, or nth elements of a sequence? 
How do we find the length of a sequence? 
### Answer
In SICP, we use `car`, `cadr`, `caddr` for the first,second, and third elements. `(length seq)` is a primitive to get the length, and `(list-ref seq n)` gets the nth element.
## Question
### Statement
What is the form of the `map` special form?
### Answer
## Question
### Statement
What are the essential differences in `fold-right` (AKA `accumulate`) and `fold-left`?
### Answer
The essential difference is that `fold-right` starts applying the operations from the right of the list and is linear recursive.

`fold-left` starts applying the operations from the left of the list and is linear iterative.

They give the same result if the binary operation is associative.

```rkt

; fold right AKA accumulate
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
(define fold-right accumulate)
(define (fold-left op initial sequence)
  (define (iter result rest)
    (if (null? rest)
        result
        (iter (op result (car rest))
              (cdr rest))))
  (iter initial sequence))
(fold-right list nil (list 1 2 3))
;(1 (2 (3 ())))

(fold-left  list nil (list 1 2 3))
;(((() 1) 2) 3)
```
## Question
### Statement
What are the arguments of `accumulate`, `fold-left`, `flatmap`, `filter`? What's their usefulness?
### Answer

The arguments are:
```rkt
(accumulate op initial sequence)
(fold-left op initial sequence)
(filter q? sequence)
(define (flatmap f sequence)
  (accumulate append nil (map f sequence))) 
```
Accumulate and fold-left are very similar, except that in the case of accumulate the first evaluation is `(op last-element initial)`
while in the case of `fold-left` the first evaluation is `(op initial first-element)`.

Filter takes all elements from a sequence for which `(q? x)` is true.

Flatmap maps $f$ to all elements in the sequence, then appends all results.
## Question
### Statement
What is dotted tail notation and how can it be used to write functions with arbitrary numbers of arguments?

### Answer

## TODO
Enumerate leaves and count leaves of a tree

Matrix operations


## Question
### Statement
### Answer
## Question
### Statement
### Answer
## Question
### Statement
### Answer
## Question
### Statement
### Answer
