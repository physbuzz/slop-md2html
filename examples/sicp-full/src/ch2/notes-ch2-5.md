<div class="nav">
    <span class="activenav"><a href="notes-ch2-4.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="../ch3/notes-ch3-1.html">Next →</a></span>
</div>


[HTML Book Chapter 2.5 Link](https://sarabander.github.io/sicp/html/2_002e5.xhtml#g_t2_002e5)

@toc

## Section 2.5

Note: At the end it looks like we talk about polynomials, it might be worth skimming over some simple algorithms from Ideals, Varieties, and Algorithms and maybe implementing a simple one. 


Note: Lagrange interpolating polynomials are cool. [https://en.wikipedia.org/wiki/Lagrange_polynomial](https://en.wikipedia.org/wiki/Lagrange_polynomial)

TODO: Skip 86

### Meeting 05-04-2025
https://sarabander.github.io/sicp/html/2_002e5.xhtml#g_t2_002e5

- [https://www.youtube.com/watch?v=kc9HwsxE1OY](The Unreasonable Effectiveness of Multiple Dispatch) and [the slides to the talk](https://www.juliaopt.org/meetings/santiago2019/slides/stefan_karpinski.pdf)
- Take a look at this [curriculum document](https://cs.brown.edu/~sk/Publications/Papers/Published/fffk-htdp-vs-sicp-journal/paper.pdf)

#### Relevant Wiki Pages:
- [Numerical tower](https://en.wikipedia.org/wiki/Numerical_tower). A more formal version of the integer &lt; rational &lt; real &lt; complex.
- [Expression problem](https://en.wikipedia.org/wiki/Expression_problem)
- [Multiple inheritance](https://en.wikipedia.org/wiki/Multiple_inheritance)
- [Common Lisp Object System](https://en.wikipedia.org/wiki/Common_Lisp_Object_System)
- [Metaobject protocol](https://en.wikipedia.org/wiki/Metaobject#Metaobject_protocol)
- [Greenspun's tenth rule](https://en.wikipedia.org/wiki/Greenspun%27s_tenth_rule)

#### Info about Julia:
- [https://juliacon.org/2025/](https://juliacon.org/2025/)

### Goofiness
- turn music back on (DONE!!!!)
- Ad break / stretch (DONE) 
- Finish recording the links (YEP YOU GUESSED IT)
- try to take over the world (seems to0 hard)
- fail (IN THE BAG!!!)
- Learn two spell
- fail
- keep doing problems

### Introduction

### Exercises

##### Solution

#### Exercise 2.77

Louis Reasoner tries to evaluate
the expression `(magnitude z)` where `z` is the object shown in
Figure 2.24.  To his surprise, instead of the answer 5 he gets an error
message from `apply-generic`, saying there is no method for the operation
`magnitude` on the types `(complex)`.  He shows this interaction to
Alyssa P. Hacker, who says "The problem is that the complex-number selectors
were never defined for `complex` numbers, just for `polar` and
`rectangular` numbers.  All you have to do to make this work is add the
following to the `complex` package:"

```rkt
(put 'real-part '(complex) real-part)
(put 'imag-part '(complex) imag-part)
(put 'magnitude '(complex) magnitude)
(put 'angle '(complex) angle)
```

Describe in detail why this works.  As an example, trace through all the
procedures called in evaluating the expression `(magnitude z)` where
`z` is the object shown in Figure 2.24.  In particular, how many
times is `apply-generic` invoked?  What procedure is dispatched to in each
case?

##### Solution

Implicitly, we must mean that we have also defined:

```rkt
(define (magnitude z)
  (apply-generic 'magnitude z))
```

So then the sequence of calls looks as follows. We make two calls to
`apply-generic`, on the first call we wind up inside the complex package,
and on the second call we wind up inside the rectangular package.

```rkt
(magnitude z)
(apply-generic 'magnitude z)
;; This calls the following inside apply-generic:
;;   (apply (get op type-tags) (map contents args))
;; type-tags is just equal to 'complex, so we call magnitude again, 
;; this time it was the magnitude scoped inside the complex package. 
;; The argument to this function is the contents of args, so inside
;; the structure ('complex . ('rectangular . (3 . 4))) we've stripped away the 'complex.
(apply-generic 'magnitude ('rectangular . (3 . 4)))
;; Inside install-rectangular-package
(magnitude (3 . 4))
5
```

Full working example:

@src(code/ex2-77.rkt, collapsed)

#### Exercise 2.78

The internal procedures in the
`scheme-number` package are essentially nothing more than calls to the
primitive procedures `+`, `-`, etc.  It was not possible to use the
primitives of the language directly because our type-tag system requires that
each data object have a type attached to it.  In fact, however, all Lisp
implementations do have a type system, which they use internally.  Primitive
predicates such as `symbol?` and `number?`  determine whether data
objects have particular types.  Modify the definitions of `type-tag`,
`contents`, and `attach-tag` from 2.4.2 so that our
generic system takes advantage of Scheme's internal type system.  That is to
say, the system should work as before except that ordinary numbers should be
represented simply as Scheme numbers rather than as pairs whose `car` is
the symbol `scheme-number`.

##### Solution

So, the point of this problem is that we can make these modifications
and that's all we need to do: we need no modifications to the 
scheme-number package.

```rkt
(define (attach-tag type-tag contents)
  (if (equal? type-tag 'scheme-number) 
      contents
      (cons type-tag contents)))
(define (type-tag datum)
  (cond ((pair? datum) (car datum))
        ((number? datum) 'scheme-number)
        (else (error "Bad tagged datum: TYPE-TAG" datum))))
(define (contents datum)
  (cond ((pair? datum) (cdr datum))
        ((number? datum) datum)
        (else (error "Bad tagged datum: CONTENTS" datum))))
```

Working example:

@src(code/ex2-78.rkt, collapsed)



#### Exercise 2.79

Define a generic equality
predicate `equ?` that tests the equality of two numbers, and install it in
the generic arithmetic package.  This operation should work for ordinary
numbers, rational numbers, and complex numbers.

##### Solution

We certainly want to do this without type coercion, because we get to
type coercion in the next sections.

```rkt
;; Inside scheme-number
  ;; This depends how it's defined. If we define it as in 2.78, 
  ;; then we can just compare the numbers directly.
  (define (equ? z1 z2) 
    (= z1 z2))
  (put 'equ? '(scheme-number scheme-number) equ?)

;; Inside rational-package
  ;; z1a/z1b = z2a/z2b  iff z1a*z2b - z2a*z1b = 0
  (define (equ? z1 z2)
    (= (- (* (numer z1) (denom z2)) 
          (* (numer z2) (denom z1)))
        0))
  (put 'equ? '(rational rational) equ?)

;;inside complex-package
  (define (equ? z1 z2)
    (and (= (real-part z1) (real-part z2)) 
         (= (imag-part z1) (imag-part z2))))
  (put 'equ? '(complex complex) equ?)

(define (equ? z1 z2)
  (apply-generic 'equ? z1 z2))
```

Testing:

@src(code/ex2-79.rkt, collapsed)

#### Exercise 2.80

Define a generic predicate
`=zero?` that tests if its argument is zero, and install it in the generic
arithmetic package.  This operation should work for ordinary numbers, rational
numbers, and complex numbers.

##### Solution

```rkt
  ;;inside scheme-number
  (put '=zero? 'scheme-number 
    (lambda (a) (= a 0)))
  ;;inside rational-package
  (put '=zero? 'rational 
    (lambda (a) (= (numer a) 0)))
  ;;inside complex-package
  (put '=zero? 'complex 
    (lambda (z) (and (= (real-part z) 0) (= (imag-part z) 0))))

(define (=zero? a)
  (apply-generic '=zero? a))
```
Testing:
@src(code/ex2-80.rkt, collapsed)


#### Exercise 2.81

Louis Reasoner has noticed that
`apply-generic` may try to coerce the arguments to each other's type even
if they already have the same type.  Therefore, he reasons, we need to put
procedures in the coercion table to coerce arguments of each type to
their own type.  For example, in addition to the
`scheme-number->complex` coercion shown above, he would do:

```rkt
(define (scheme-number->scheme-number n) n)
(define (complex->complex z) z)

(put-coercion 'scheme-number 'scheme-number
              scheme-number->scheme-number)

(put-coercion 'complex 'complex 
              complex->complex)
```

**1.** With Louis's coercion procedures installed, what happens if
`apply-generic` is called with two arguments of type `scheme-number`
or two arguments of type `complex` for an operation that is not found in
the table for those types?  For example, assume that we've defined a generic
exponentiation operation:

```rkt
(define (exp x y) 
  (apply-generic 'exp x y))
```


and have put a procedure for exponentiation in the Scheme-number
package but not in any other package:

```rkt
;; following added to Scheme-number package
(put 'exp 
     '(scheme-number scheme-number)
     (lambda (x y) 
       (tag (expt x y)))) 
       ; using primitive expt
```


What happens if we call `exp` with two complex numbers as arguments?

**2.** Is Louis correct that something had to be done about coercion with arguments of
the same type, or does `apply-generic` work correctly as is?

**3.** Modify `apply-generic` so that it doesn't try coercion if the two
arguments have the same type.

##### Solution
So first of all, it should be fine with no definitions. We do two extra lookups,
which both return false to say there is no coercion from type A to type A,
and then we give an error. But let's suppose we do this anyways.

**Part 1.**
`proc` is false, but we now find coercion functions
`t1->t2` and `t2->t1`, but the first call to this function introduces a problem:
```rkt
(apply-generic op (t1->t2 a1) a2)
```
We apply the lookup again, proc is false, we coerce and call apply-generic again...
so we just get an infinite recursion!

**Part 2.** `apply-generic` works fine as-is. If the function isn't found 
and assigned to proc, then there's nothing we can do, we want `t1->t2` and `t2->t1` to be false exactly as they are.

**Part 3.** We really don't need this, but we could check for `eq?` among
the two types. After we check to make sure that the length is two and 
after we use `let` to get the two types, we check for type equality.

```rkt
(define (apply-generic op . args)
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (if (= (length args) 2)
              (let ((type1 (car type-tags))
                    (type2 (cadr type-tags))
                    (a1 (car args))
                    (a2 (cadr args)))
                (if (eq? type1 type2)  ;; <-- our modification
                  (error "No method for these types"
                    (list op type-tags))
                  (let ((t1->t2
                         (get-coercion type1
                                       type2))
                        (t2->t1
                         (get-coercion type2
                                       type1)))
                    (cond (t1->t2
                           (apply-generic
                            op (t1->t2 a1) a2))
                          (t2->t1
                           (apply-generic
                            op a1 (t2->t1 a2)))
                          (else
                           (error
                            "No method for
                             these types"
                            (list
                             op
                             type-tags)))))))
              (error
               "No method for these types"
               (list op type-tags)))))))
```

#### Exercise 2.82

Show how to generalize
`apply-generic` to handle coercion in the general case of multiple
arguments.  One strategy is to attempt to coerce all the arguments to the type
of the first argument, then to the type of the second argument, and so on.
Give an example of a situation where this strategy (and likewise the
two-argument version given above) is not sufficiently general.  (Hint: Consider
the case where there are some suitable mixed-type operations present in the
table that will not be tried.)

##### Solution
Well, this is a really shoddy type conversion system! Let's implement it like 
the book asks. But of course it won't be sufficient, say we wanted to define
`fast-pow` from chapter 1 as `(fast-pow complex int)`. Our type conversion
system would miss this.

I ended up with a very overcomplicated method to do this, I wanted to power
through it but it's definitely worth comparing to other solutions to see
if they did it a simpler way.

```rkt
;; Try to coerce every element of args into target-type (a single type).
;; If a coercion fails to exist, or if the function on type (target-type
;; target-type ...) doesn't exist, return false.
(define (coerce-all target-type args) 
  ;; get the function f that coerces source-type to target-type if it 
  ;; exists, identity lambda if it's the same type, and false otherwise.
  (define (coerce-function source-type) 
    (let ((coercion (get-coercion source-type target-type)))
      (if coercion 
          coercion
          (if (eq? source-type target-type)
            (lambda (x) x)
            #f))))
        
  ;; Coerce all arguments if all type coercions exist, else return false.
  (define (map-if-exists procs args)
    (if (= (length procs) (length args))
      (if (null? procs) '() 
        (let ((coercion (car procs)) (x (car args)))
          (if coercion
              (let ((rest (map-if-exists (cdr procs) (cdr args))))
                (if rest 
                    (cons (coercion x) rest)
                    #f))
              #f)))
      (error "procs and args must be the same length inside coerce-all")))
  (let ((type-tags (map type-tag args)))
    (let ((procs (map coerce-function type-tags)))
      (map-if-exists procs args))))

(define (apply-generic op . args)
  ;; Attempt the coerction to the nth type. 
  ;; The car of the result will be false if no function and coercion exists
  ;; If one does exist, the car will be true and the cadr will be the result.
  (define (attempt-coercions n type-tags args)
    ;; So long as n<=length(type-tags) try to look up a function 
    ;; with type tags all of (list-ref type-tags n). If not, increase n by one
    ;; and try again.
    (if (< n (length type-tags))
      (let ((target-type (list-ref type-tags n)))
        (let ((proc (get op (map (lambda (x) target-type) type-tags)))
              (args-coerced (coerce-all target-type args)))
          (if (and proc args-coerced)
              (list #t (apply proc (map contents args-coerced)))
            (attempt-coercions (+ n 1) type-tags args))))
       (list #f )))
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (if (> (length args) 1)
            (let ((res (attempt-coercions 0 type-tags args)))
              (if (car res)
                (cadr res)
                (error
                 "No method for these types!!!"
                 (list op type-tags))))
            (error
             "No method for these types"
             (list op type-tags)))))))
```

Because this is so much code, I wanted to run a bunch of test cases for it:

@src(code/ex2-82.rkt, collapsed)

Other solutions include...

 - [This solution](https://github.com/kana/sicp/blob/master/ex-2.82.scm) using square brackets for everything, which isn't a language feature I've used yet.
 - [This solution](https://wizardbook.wordpress.com/2010/12/08/exercise-2-82/) which uses `member` and `(map func list1 list2)`. In Python this would be something like `[func(a,b) for (a,b) in zip(list1,list2)]`.
 - [This solution](https://github.com/track02/Scheme---SICP/blob/master/Ex%202.82%20-%20Generics.scm) is a much better / shorter implementation of what I did. 

#### Exercise 2.83

Suppose you are designing a
generic arithmetic system for dealing with the tower of types shown in
Figure 2.25: integer, rational, real, complex.  For each type (except
complex), design a procedure that raises objects of that type one level in the
tower.  Show how to install a generic `raise` operation that will work for
each type (except complex).

##### Solution

We want something like this. Of course scheme-number might be just an untagged
number, and `real` might be an untagged floating point number, so we have to assume
`contents` takes care of that properly.

```rkt
  ;; inside scheme-number
  (put 'raise '(scheme-number)
    (lambda (a) ((get 'make 'rational) (contents a) 1)))

  ;; inside rational package
  (put 'raise '(rational)
    (lambda (rat) (
      (apply-generic 'div ((get 'make 'real) (numer rat)) 
                          ((get 'make 'real) (denom rat))))))

  ;; inside real package
  (put 'raise '(real)
    (lambda (r) ((get 'make 'complex) (contents real) 0) ))
```

#### Exercise 2.84

Using the `raise` operation
of Exercise 2.83, modify the `apply-generic` procedure so that it
coerces its arguments to have the same type by the method of successive
raising, as discussed in this section.  You will need to devise a way to test
which of two types is higher in the tower.  Do this in a manner that is
compatible with the rest of the system and will not lead to problems in
adding new levels to the tower.
##### Solution

Let's use our solution to 2.82. 
All we need to do is implement `coerce-all` in this new context, and everything will work. 

```rkt
;; Use accumulate from chapter 2-2.
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))

;; returns (list #t raised-result) if repeated application of raise can turn 
;; source into target. Returns (list #f) otherwise.
(define (raise-recurse argument target-type) 
  (let ((source-type (type-tag argument)))
    (if (eq? source-type target-type)
        (list #t argument)
        (let ((raise-func (get 'raise (list source-type))))
          (if raise-func
            (raise-recurse (raise-func (contents argument)) target-type)
            (list #f))))))

(define (coerce-all target-type args) 
  ;; The point of this is that when we apply (map (... raise-recurse ) args),
  ;; we get a list list ((#t coerced) (#t coerced) (#f) (#t coerced))
  ;; If anything is false, then we fail.
  ;; If all are true, then we return a list (list #t coerced-list)
  ((lambda (args-coerced) (if (car args-coerced) (cadr args-coerced) #f))
    (accumulate (lambda (x y) 
                  (if (and (car x) (car y))
                    (list #t (cons (cadr x) (cadr y)))
                    (list #f))) 
              (list #t '()) 
              (map (lambda (arg) (raise-recurse arg target-type)) args))))

;; The rest is the same as in 2-82, all we've done is replace coerce-all to work
;; by repeated application of raise.
(define (apply-generic op . args)
  (define (attempt-coercions n type-tags args)
    (if (< n (length type-tags))
      (let ((target-type (list-ref type-tags n)))
        (let ((proc (get op (map (lambda (x) target-type) type-tags)))
              (args-coerced (coerce-all target-type args)))
          (if (and proc args-coerced)
              (list #t (apply proc (map contents args-coerced)))
            (attempt-coercions (+ n 1) type-tags args))))
       (list #f )))
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (if (> (length args) 1)
            (let ((res (attempt-coercions 0 type-tags args)))
              (if (car res)
                (cadr res)
                (error
                 "No method for these types!!!"
                 (list op type-tags))))
            (error
             "No method for these types"
             (list op type-tags)))))))
```

Working example:

@src(code/ex2-84.rkt, collapsed)

#### Exercise 2.85

This section mentioned a method
for simplifying a data object by lowering it in the tower of types as far
as possible.  Design a procedure `drop` that accomplishes this for the
tower described in Exercise 2.83.  The key is to decide, in some general
way, whether an object can be lowered.  For example, the complex number 
$1.5 + 0i$ can be lowered as far as `real`, the complex number $1 + 0i$ can
be lowered as far as `integer`, and the complex number $2 + 3i$ cannot
be lowered at all.  Here is a plan for determining whether an object can be
lowered: Begin by defining a generic operation `project` that pushes
an object down in the tower.  For example, projecting a complex number would
involve throwing away the imaginary part.  Then a number can be dropped if,
when we `project` it and `raise` the result back to the type we
started with, we end up with something equal to what we started with.  Show how
to implement this idea in detail, by writing a `drop` procedure that drops
an object as far as possible.  You will need to design the various projection
operations and
install `project` as a generic operation in the system.  You will also
need to make use of a generic equality predicate, such as described in
Exercise 2.79.  Finally, use `drop` to rewrite `apply-generic`
from Exercise 2.84 so that it simplifies its answers.

##### Solution

Let's assume that we have the solution to 2.84 and 2.79. Then we can just 
do something like `(equ? (drop arg) arg)` and the raising will be handled for us,
using the code of 2.84.

First of all, since we're changing apply-generic I found that I had some 
unintended side-effects with my 'raise rational definition. So I change that definition
too.

```rkt
  ;; inside rational package
  (put 'project '(rational) (lambda (rat) 
    (/ (- (numer rat) (remainder (numer rat) (denom rat))) (denom rat))))
  (put 'raise '(rational)
    (lambda (rat) 
      ((get 'make-from-real-imag 'complex) (/ (numer rat) (denom rat)) 0)))
  ;; inside complex package
  (put 'project '(complex) (lambda (z) 
    ((get 'make 'rational) (real-part z) 1)))

(define (drop arg)
  (let ((proj-proc (get 'project (type-tag arg))))
    (if (not proj-proc) 
      arg
      (let ((projected-arg (proj-proc (contents arg))))
        (let ((raise-proc (get 'raise (type-tag projected-arg))))
          (if (not raise-proc) 
            (error "type is projected to but has no raise function!" projected-arg)
            (let ((raised-projected-arg (raise-proc projected-arg))
                  (equ? (get 'equ? (list (type-tag arg) (type-tag arg)))))
                  (if (equ? arg raised-projected-arg)
                     (drop projected-arg)
                     arg))))))))
```

@src(code/ex2-85.rkt, collapsed)

#### Exercise 2.86

Suppose we want to handle complex
numbers whose real parts, imaginary parts, magnitudes, and angles can be either
ordinary numbers, rational numbers, or other numbers we might wish to add to
the system.  Describe and implement the changes to the system needed to
accommodate this.  You will have to define operations such as `sine` and
`cosine` that are generic over ordinary numbers and rational numbers.

##### Solution

Inside the complex numbers packages, we have to make sure that we always use
`apply-generic 'mul` instead of `*`, and we also have to make sure to use
`apply-generic 'sin` instead of `sin`, as well as define the sine and 
cosine generic functions inside the other packages. I'll omit defining 
the sine and cosine of complex numbers, but this can be done using the 
hyperbolic trig functions and/or exponentials.

@src(code/ex2-86.rkt, collapsed)



#### Exercise 2.87

Install `=zero?` for
polynomials in the generic arithmetic package.  This will allow
`adjoin-term` to work for polynomials with coefficients that are
themselves polynomials.

##### Solution

I make use of the `accumulate` function.
Ideally, we'd prevent the construction of terms with zero coefficients, but that doesn't seem
to be the approach we're taking so we have to check each coef individually.

```rkt
  (define (=zero?-poly poly)
    (accumulate (lambda (x y) (and y (=zero? (coeff x))))
                #t
                (term-list poly)))
  ;; Make sure to install the function
  (put '=zero? '(polynomial) =zero?-poly)
```


@src(code/ex2-87.rkt, collapsed)

#### Exercise 2.88

Extend the polynomial system to
include subtraction of polynomials.  (Hint: You may find it helpful to define a
generic negation operation.)

##### Solution

Let's add a generic `'negate`. We do have to define negate for the other types as well.

```rkt
;; Exercise 2-88. 
;; Inside the polynomial package.
(define (negate-terms L) 
  (if (empty-termlist? L)
    L
    (let ((t (first-term L)) (r (rest-terms L)))
      (adjoin-term (make-term (order t) (apply-generic 'negate (coeff t)))
                   (negate-terms r)))))
(define (sub-terms L1 L2)
  (add-terms L1 (negate-terms L2)))
(define (sub-poly p1 p2)
  (if (same-variable? (variable p1)
                      (variable p2))
    (make-poly
     (variable p1)
     (sub-terms (term-list p1)
                (term-list p2)))
    (error "Polys not in same var:
           SUB-POLY"
           (list p1 p2))))
(put 'sub '(polynomial polynomial)
     (lambda (p1 p2) 
       (tag (sub-poly p1 p2))))
(put 'negate '(polynomial)
     (lambda (p) 
       (tag (make-poly (variable p) (negate-terms (term-list p))))))
```

Generic negate:
```rkt
  (put 'negate '(scheme-number)
       (lambda (x) (- x)))
  (put 'negate '(rational)
       (lambda (r) (tag (make-rat (- (numer r)) (denom r)))))
  (put 'negate '(polar)
       (lambda (z) (tag (make-from-mag-ang (magnitude z) (+ (angle z) pi)))))
  (put 'negate '(rectangular)
       (lambda (z) (tag (make-from-real-imag (- (real-part z) (- (imag-part z)))))))

```
Full code:

@src(code/ex2-88.rkt, collapsed)




#### Exercise 2.89

Define procedures that implement
the term-list representation described above as appropriate for dense
polynomials.

##### Solution

Let's define an `install-dense-polynomial-package`. Some changes that have to be made are:

- We no longer have `order` or `coeff` functions that can be applied to each term.
- Addition is now much simpler, but we have to rewrite multiplication

First, inside `make-poly` I chop off leading zeros (we can't chop off trailing zeros):

```rkt
  ;; Chop off the leading zeros of a term list.
  (define (chop-leading-zeros L)
    (cond ((null? L) L)
          ((apply-generic '=zero? (car L)) (chop-leading-zeros (cdr L)))
          (else L)))
  (define (make-poly variable term-list)
    (cons variable (chop-leading-zeros term-list)))
```

Addition is somewhat simple. Note that the order of the algorithm is much worse than it needs to be 
because of my calls to `length`. There's probably some trick we can do to avoid this overhead by thinking
about tail recursive or linear recursive algorithms, but I just wanted to get this working. Also note that
`add-poly` is the same as before with no changes, it just calls the `add-terms` function.
```rkt
  (define (add-terms L1 L2)
    (let ((length1 (length L1)) (length2 (length L2)))
      ;; divide into cases. If L2 is longer, swap the terms
      (cond ((< length1 length2) (add-terms L2 L1))
            ;; if the lengths are equal, add term by term
            ((= length1 length2) 
              (map (lambda (x y) 
                     (apply-generic 'add x y)) 
                   L1 
                   L2))
            ;; else, shorten the longer list.
            (else (cons (car L1) (add-terms (cdr L1) L2))))))
```

Multiplication is a bit more complicated. I define functions `map-indexed`
and `make-zero-terms`. Then, I follow the same approach as the polynomial package.
First we define (monomial) $\times$ (term list) multiplication, and then use this to 
build (term list) $\times$ (term list) multiplication.
```rkt
  ;; Note: this is NOT generic if we don't have type coercion. 
  ;; We could define a ((get 'make-zero type)) to make it generic.
  (define (make-zero-terms l)
    (if (= l 0) '() (cons 0 (make-zero-terms (- l 1)))))
  ;; returns the term list representing 
  ;; (coeff)*(variable)^order * (polynomial represented by L)
  (define (mul-term-by-all-terms order coeff L)
    (if (null? L)
      '()
      (append (map (lambda (x) 
                     (apply-generic 'mul x coeff)) 
                   L)  
              (make-zero-terms order))))
  ;; Define a map-indexed function. (map-indexed f '(a b c)) is
  ;; ((f a 0) (f b 1) (f c 2))
  (define (map-indexed my-lambda lst)
    (define (map-indexed-inner lst-cur counter)
      (if (null? lst-cur) '()
      (cons (my-lambda (car lst-cur) counter) (map-indexed-inner (cdr lst-cur) (+ counter 1)))))
    (map-indexed-inner lst 0))
  (define (mul-terms L1 L2)
    (let ((length1 (length L1)) (length2 (length L2)))
      (cond ((< length1 length2) (mul-terms L2 L1))
            ((= length2 0) '())
            (else 
              (accumulate 
                (lambda (Lx Ly) (add-terms Lx Ly))
                '()
                (map-indexed 
                  (lambda (coeff ctr) 
                    ;; multiply L2 polynomial by the term x*(var)^(order).
                    (mul-term-by-all-terms (- (- length1 ctr) 1) coeff L2))
                  L1))))))
```


@src(code/ex2-89.rkt, collapsed)

#### Exercise 2.90

Suppose we want to have a
polynomial system that is efficient for both sparse and dense polynomials.  One
way to do this is to allow both kinds of term-list representations in our
system.  The situation is analogous to the complex-number example of 
2.4, where we allowed both rectangular and polar representations.  To do
this we must distinguish different types of term lists and make the operations
on term lists generic.  Redesign the polynomial system to implement this
generalization.  This is a major effort, not a local change.

##### Solution
We already have most things handled. Firstly, I renamed the tags to `sparse-poly` and `dense-poly`. 
There are six generic functions for our polynomial package:
`'add`, `'sub`, `'mul`, `'negate`, `'=zero?`, and `'make`. We should expand this into `'make-dense-polynomial` and
`'make-sparse-polynomial`.

```rkt
(install-sparse-polynomial-package)
(install-dense-polynomial-package)
(define (install-polynomial-package)
  (define (tag p) (attach-tag 'polynomial p))
  (put '=zero? '(polynomial)
       (lambda (p) (apply-generic '=zero? p)))
  (put 'negate '(polynomial)
       (lambda (p) (tag (apply-generic 'negate p))))
  (put 'make-sparse-polynomial 'polynomial
       (lambda (var terms) 
         (tag ((get 'make 'sparse-poly) var terms))))
  (put 'make-dense-polynomial 'polynomial
       (lambda (var terms) 
         (tag ((get 'make 'dense-poly) var terms))))
...)
```

The only difficult remaining thing would be handling operations involving
two different types of polynomials, depending on how we've implemented type coercion.
I handle this by converting to sparse - sparse operations by default.

```rkt
(define (dense-poly->sparse-poly dense)
  (let ((var (car dense)) 
        (terms (cdr dense)) 
        (order (length (cdr dense))))
    ((get 'make 'sparse-poly) 
        var 
        (map-indexed (lambda (term index) (list (- (- order index) 1) term)) terms))))
(define (put-poly-symb symb)
  (put symb '(polynomial polynomial)
       (lambda (p1 p2) 
         (tag 
           (let ((t1 (type-tag p1)) (t2 (type-tag p2)))
             (cond ((eq? t1 t2) (apply-generic symb p1 p2))
                   ((and (eq? t1 'sparse-poly)
                         (eq? t2 'dense-poly)) 
                    (apply-generic symb p1 (dense-poly->sparse-poly (contents p2))))
                   ((and (eq? t1 'dense-poly)
                         (eq? t2 'sparse-poly)) 
                    (apply-generic symb (dense-poly->sparse-poly (contents p1)) p2))
                   (else (error "Symbol called with polynomials of invalid types:" symb t1 t2))))))))
(put-poly-symb 'add)
(put-poly-symb 'mul)
(put-poly-symb 'sub)
```

Working code test:

@src(code/ex2-90.rkt,collapsed)

#### Exercise 2.91

A univariate polynomial can be
divided by another one to produce a polynomial quotient and a polynomial
remainder.  For example,

$${x^5 - 1 \over x^2 - 1} \,=\, {x^3 + x,} \text{  remainder  } {x - 1.}  $$

Division can be performed via long division.  That is, divide the highest-order
term of the dividend by the highest-order term of the divisor.  The result is
the first term of the quotient.  Next, multiply the result by the divisor,
subtract that from the dividend, and produce the rest of the answer by
recursively dividing the difference by the divisor.  Stop when the order of the
divisor exceeds the order of the dividend and declare the dividend to be the
remainder.  Also, if the dividend ever becomes zero, return zero as both
quotient and remainder.

We can design a `div-poly` procedure on the model of `add-poly` and
`mul-poly`. The procedure checks to see if the two polys have the same
variable.  If so, `div-poly` strips off the variable and passes the
problem to `div-terms`, which performs the division operation on term
lists. `Div-poly` finally reattaches the variable to the result supplied
by `div-terms`.  It is convenient to design `div-terms` to compute
both the quotient and the remainder of a division.  `Div-terms` can take
two term lists as arguments and return a list of the quotient term list and the
remainder term list.

Complete the following definition of `div-terms` by filling in the missing
expressions.  Use this to implement `div-poly`, which takes two polys as
arguments and returns a list of the quotient and remainder polys.

```rkt
(define (div-terms L1 L2)
  (if (empty-termlist? L1)
      (list (the-empty-termlist) 
            (the-empty-termlist))
      (let ((t1 (first-term L1))
            (t2 (first-term L2)))
        (if (> (order t2) (order t1))
            (list (the-empty-termlist) L1)
            (let ((new-c (div (coeff t1) 
                              (coeff t2)))
                  (new-o (- (order t1) 
                            (order t2))))
              (let ((rest-of-result
                     ⟨compute rest of result recursively}⟩ ))
                ⟨form complete result⟩ ))))))
```


##### Solution

Given the new term $t$, we have:

$$\frac{P_1}{P_2} =\frac{P_1- t P_2+t P_2}{P_2} = t + \frac{P_1-t P_2}{P_2}$$
And the whole idea behind long division is to choose $t$ so that the leading term of $P_1$ cancels.
I do this subtraction using the function `sub-terms` which I defined in problem 2.88.

```rkt
(define (div-terms L1 L2)
  (if (empty-termlist? L1)
      (list (the-empty-termlist) 
            (the-empty-termlist))
      (let ((t1 (first-term L1))
            (t2 (first-term L2)))
        (if (> (order t2) (order t1))
            (list (the-empty-termlist) L1)
            (let ((new-c (apply-generic 'div (coeff t1) 
                                             (coeff t2)))
                  (new-o (- (order t1) 
                            (order t2))))
              (let ((new-t (make-term new-o new-c)))
                (let ((rest-of-result
                       (div-terms 
                         (sub-terms L1 (mul-term-by-all-terms new-t L2)) 
                         L2)))
                  (let ((div-val (car rest-of-result))
                        (rem-val (cadr rest-of-result)))
                    (list (add-terms (list new-t) div-val)
                          rem-val)))))))))
```


Also, in order to do the plumbing for everything, I define 
```rkt
(define (div-poly p1 p2)
  (if (same-variable? (variable p1)
                      (variable p2))
    (let ((res (div-terms (term-list p1)
                (term-list p2))))
       (list (make-poly (variable p1) (car res)) (make-poly (variable p1) (cadr res))))
    (error "Polys not in same var:
           SUB-POLY"
           (list p1 p2))))
(put 'div-poly '(polynomial polynomial) 
     (lambda (p1 p2)
       (let ((res (div-poly p1 p2)))
         (list (tag (car res)) (tag (cadr res))))))
```

@src(code/ex2-91.rkt, collapsed)

#### Exercise 2.92

By imposing an ordering on
variables, extend the polynomial package so that addition and multiplication of
polynomials works for polynomials in different variables.  (This is not easy!)

##### Solution
We have a few different options here:

- We could have a `set` of monomials. 
- We could replace `variables` with `variable-list` and use the ordering imposed by that list.
- We could define a lexicographic ordering over symbols and monomials.

I'm going with the third option. The monomial $C x^a y^b$ 
will be represented as `(list (list (list 'x a) (list 'y b)) C)`. So now, `(coeff term)` still behaves the same,
but `(order term)` gives the order of the lits of variables.

First, let's make sure I can define the ordering on monomials properly:

@src(code/ex2-92b.rkt, collapsible)

Next, we can define a function to create a correct polynomial from a 
unsorted list of monomials (unsorted because I can never remember the 
correct way to do things). 

```rkt
(define (install-polynomial-package)
  (define (single-order<? so1 so2)
    (or (symbol<? (car so1) (car so2))
        (< (cadr so2) (cadr so1))))
  (define (order<? o1 o2)
    (cond 
      ((null? o1) #f)
      ((null? o2) #t)
      ((< (length o2) (length o1)) #t)
      ((single-order<? (car o1) (car o2)) #t)
      ((single-order<? (car o2) (car o1)) #f)
      (else (order<? (cdr o1) (cdr o2)))))

  ;; Term list should be a list of (list coeff monomial)
  ;; monomial is of the form '((x 3) (y 2) (z 4)) to represent x^3*y^2*z^4.
  (define (make-mono coeff order) (list coeff order)) 
  (define (coeff mono) (car mono))
  (define (order mono) (cadr mono))
  (define (make-poly-from-unsorted term-list)
    (define (sort-monomial mono) 
      (make-mono (coeff mono) (sort (order mono) single-order<?)))
    (define (monomial-compare x y) 
      (order<? (order x) (order y)))
    (sort (map sort-monomial term-list) monomial-compare))
  (define (tag p) (attach-tag 'polynomial p))
  (put 'make 'polynomial
       (lambda (terms) 
         (tag (make-poly-from-unsorted terms))))
  ...
  'done)
```

Now, `add-poly` is going to be basically the same as add-terms, 
except instead of `<` to compare orders, we'll have to use `order<?`. 
We'll also have to define `adjoin-term` correctly.
`negate` and `sub` are easy. 

Testing some polynomial multiplication examples:

@src(code/ex2-92.rkt, collapsed)

#### Exercise 2.93

Modify the rational-arithmetic
package to use generic operations, but change `make-rat` so that it does
not attempt to reduce fractions to lowest terms.  Test your system by calling
`make-rational` on two polynomials to produce a rational function:

```rkt
(define p1 (make-polynomial 'x '((2 1) (0 1))))
(define p2 (make-polynomial 'x '((3 1) (0 1))))
(define rf (make-rational p2 p1))
```

Now add `rf` to itself, using `add`. You will observe that this
addition procedure does not reduce fractions to lowest terms.

##### Solution

We have the following rational function

$$r_f = \frac{x^3+1}{x^2+1}$$

We add rational numbers by doing

$$\frac{a}{b}+\frac{c}{d} = \frac{ad+bc}{bd}$$

According to this rule

<div>$$2 r_f = \frac{2(x^3+1)(x^2+1)}{(x^2+1)^2} =\frac{2x^5+2x^3+2x^2+2}{x^4+2x^2+1}$$</div>

@src(code/ex2-93.rkt, collapsed)

#### Exercise 2.94

Using `div-terms`, implement
the procedure `remainder-terms` and use this to define `gcd-terms` as
above.  Now write a procedure `gcd-poly` that computes the polynomial
GCD of two polys.  (The procedure should signal an error if the two
polys are not in the same variable.)  Install in the system a generic operation
`greatest-common-divisor` that reduces to `gcd-poly` for polynomials
and to ordinary `gcd` for ordinary numbers.  As a test, try

```rkt
(define p1 
  (make-polynomial 
   'x '((4 1) (3 -1) (2 -2) (1 2))))

(define p2 
  (make-polynomial 
   'x '((3 1) (1 -1))))

(greatest-common-divisor p1 p2)
```

and check your result by hand.

##### Solution
Let's do it by hand first. Writing this out in excruciating detail...

<div>$$\begin{align*}
\textrm{gcd}(x^4-x^3-2x^2+2x,x^3-x) &=\textrm{gcd}(x^3-x ,\textrm{mod}(x^4-x^3-2x^2+2x, x^3-x))
\end{align*}$$</div>

<div>$$\begin{align*}
\textrm{mod}(x^4-x^3-2x^2+2x, x^3-x)&=\textrm{mod}(x^4-x^3-2x^2+2x - (x-1)(x^3-x), x^3-x)\\
&=\textrm{mod}(x^4-x^3-2x^2+2x - (x^4-x^3-x^2+x), x^3-x)\\
&=\textrm{mod}(-x^2+x, x^3-x)\\
&=-x^2+x\\
\end{align*}$$</div>

<div>$$\begin{align*}
\textrm{gcd}(x^4-x^3-2x^2+2x,x^3-x) &=\textrm{gcd}(x^3-x ,-x^2+x))\\
&=\textrm{gcd}(-x^2+x,\textrm{mod}(x^3-x,-x^2+x))\\
\end{align*}$$</div>

<div>$$\begin{align*}
\textrm{mod}(x^3-x,-x^2+x) &= \textrm{mod}(x^3-x + x(-x^2+x),-x^2+x)\\
 &= \textrm{mod}(x^2-x,-x^2+x)\\
 &= 0
\end{align*}$$</div>
<div>$$\begin{align*}
\textrm{gcd}(x^4-x^3-2x^2+2x,x^3-x) &=\textrm{gcd}(x^3-x ,-x^2+x))\\
&=\textrm{gcd}(-x^2+x,0)\\
&=-x^2+x
\end{align*}$$</div>

Checking, we do in fact get the same result.

@src(code/ex2-94.rkt, collapsed)

#### Exercise 2.95

Define $P_1$, $P_2$, and
$P_3$ to be the polynomials

$$\begin{array}{rl}
  P_1:  &   x^2 - 2x + 1, \\
  P_2:  &   11x^2 + 7,    \\
  P_3:  &   13x + 5.
\end{array}
$$

Now define $Q_1$ to be the product of $P_1$ and $P_2$, and $Q_2$ to be
the product of $P_1$ and $P_3$, and use `greatest-common-divisor`
(Exercise 2.94) to compute the GCD of $Q_1$ and $Q_2$.
Note that the answer is not the same as $P_1$.  This example introduces
noninteger operations into the computation, causing difficulties with the
GCD algorithm.  To understand what is happening, try tracing
`gcd-terms` while computing the GCD or try performing the
division by hand.

##### Solution

@src(code/ex2-95.rkt, collapsed)

This is just a general fact of Euclidean domains. The GCD is only defined up to multiplication
by invertible elements. Most applications would choose to normalize the leading term to 1,
in which case we get back the polynomial $x^2-2x+1.$

#### Exercise 2.96

**1.** Implement the procedure `pseudoremainder-terms`, which is just like
`remainder-terms` except that it multiplies the dividend by the
integerizing factor described above before calling `div-terms`.  Modify
`gcd-terms` to use `pseudoremainder-terms`, and verify that
`greatest-common-divisor` now produces an answer with integer coefficients
on the example in Exercise 2.95.

**2.** The GCD now has integer coefficients, but they are larger than those
of $P_1$.  Modify `gcd-terms` so that it removes common factors from the
coefficients of the answer by dividing all the coefficients by their (integer)
greatest common divisor.

##### Solution

**For part 1,** it's just an exercise in computing the correct power of c.
I use `mul-term-by-all-terms` to perform the scalar multiplication.

```rkt
  (define (term-order L)
    (if (null? L) 0
      (order (first-term L))))
  (define (pow a b)
    (if (= b 0) 1 (* a (pow a (- b 1)))))
  (define (pseudoremainder-terms L1 L2)
    (let ((o1 (term-order L1)) 
          (o2 (term-order L2))
          (c (coeff (first-term L2))))
      (remainder-terms 
        (mul-term-by-all-terms 
          (list 0 (pow c (+ 1 (- o1 o2)))) 
          L1)
       L2)))
```

With this change alone, we end up printing out the polynomial
`('polynomial 'x ((2 1458) (1 -2916) (0 1458)))` which isn't reduced.

**For part 2,** I use accumulate to find the gcd of all the coefficients,
then apply `remove-common-factors` inside the gcd function.

```rkt
  (define (remove-common-factors L)
    (let ((common-factor
           (accumulate (lambda (x y) (gcd x y))
                (coeff (car L))
                (map coeff (cdr L)))))
      (map (lambda (x) (make-term (order x) (/ (coeff x) common-factor))) L)))
  (define (gcd-terms L1 L2)
    (remove-common-factors
      (if (=zero?-terms L2)
        L1
        (gcd-terms L2 (pseudoremainder-terms L1 L2)))))
```

Working example:

@src(code/ex2-96.rkt, collapsed)

#### Exercise 2.97

**1.** Implement this algorithm as a procedure `reduce-terms` that takes two term
lists `n` and `d` as arguments and returns a list `nn`,
`dd`, which are `n` and `d` reduced to lowest terms via the
algorithm given above.  Also write a procedure `reduce-poly`, analogous to
`add-poly`, that checks to see if the two polys have the same variable.
If so, `reduce-poly` strips off the variable and passes the problem to
`reduce-terms`, then reattaches the variable to the two term lists
supplied by `reduce-terms`.

**2.** Define a procedure analogous to `reduce-terms` that does what the original
`make-rat` did for integers:

```rkt
(define (reduce-integers n d)
  (let ((g (gcd n d)))
    (list (/ n g) (/ d g))))
```

and define `reduce` as a generic operation that calls `apply-generic`
to dispatch to either `reduce-poly` (for `polynomial` arguments) or
`reduce-integers` (for `scheme-number` arguments).  You can now
easily make the rational-arithmetic package reduce fractions to lowest terms by
having `make-rat` call `reduce` before combining the given numerator
and denominator to form a rational number.  The system now handles rational
expressions in either integers or polynomials.  To test your program, try the
example at the beginning of this extended exercise:

```rkt
(define p1 
  (make-polynomial 'x '((1 1) (0 1))))
(define p2 
  (make-polynomial 'x '((3 1) (0 -1))))
(define p3 
  (make-polynomial 'x '((1 1))))
(define p4 
  (make-polynomial 'x '((2 1) (0 -1))))
(define rf1 (make-rational p1 p2))
(define rf2 (make-rational p3 p4))
(add rf1 rf2)
```

See if you get the correct answer, correctly reduced to lowest terms.

##### Solution

**Part 1:** Here's what I did for reduce:

```rkt
  (define (reduce-terms L1 L2)
    (let ((my-gcd (gcd-terms L1 L2)))
      (let ((o1 (max (term-order L1) (term-order L2))) 
            (o2 (term-order my-gcd))
            (c (coeff (first-term my-gcd))))
        (let ((numer-list (div-terms 
                       (mul-term-by-all-terms 
                         (list 0 (pow c (+ 1 (- o1 o2)))) 
                         L1)
                       my-gcd))
              (denom-list (div-terms 
                       (mul-term-by-all-terms 
                         (list 0 (pow c (+ 1 (- o1 o2)))) 
                         L2)
                       my-gcd)))
          (list (car numer-list) (car denom-list))))))

  (define (reduce-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (map (lambda (L) (make-poly (variable p1) L))
             (reduce-terms (term-list p1) (term-list p2)))
      (error "Polys not in same var:
             REDUCE-POLY"
             (list p1 p2))))
  (put 'reduce '(polynomial polynomial)
       (lambda (p1 p2) 
         (map tag (reduce-poly p1 p2))))
```

**Part 2** We change the make-rational function to look like this:
```rkt
  (define (make-rat n d)
    (let ((red (apply-generic 'reduce n d)))
      (cons (car red) (cadr red))))
```

Demonstrate that it works:

@src(code/ex2-97.rkt, collapsed)

Important note: I've just focused on getting things that work for our test cases of integer polynomials, I can't guarantee that everything works correctly, especially in case rational numbers sneak into the objects without me noticing, or we get division by zero or that sort of thing! This can definitely be rewritten in a better way.
