<div class="nav">
    <span class="activenav"><a href="notes-ch2-3.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch2-5.html">Next →</a></span>
</div>


[HTML Book Chapter 2.4 Link](https://sarabander.github.io/sicp/html/2_002e4.xhtml#g_t2_002e4)

@toc

## Section 2.4

### Meeting 04-27-2025

- https://www.gnu.org/software/emacs/manual/html_node/elisp/Association-Lists.html
- https://www.cs.cmu.edu/Groups/AI/util/html/cltl/clm/node108.html
- https://en.wikipedia.org/wiki/Object-oriented_programming#History

### Other
For this section, we have to use code that we don't know how to write yet, fun times.

- SICP Guile handles it here: [https://github.com/zv/SICP-guile/blob/master/sicp2.rkt#L1982](https://github.com/zv/SICP-guile/blob/master/sicp2.rkt#L1982)
- This github repo handles it a different way: [https://mk12.github.io/sicp/exercise/2/4.html](https://mk12.github.io/sicp/exercise/2/4.html)
- I handle `get` and `put` this way:

@src(code/package-example.rkt)

@src(code/package-example2.rkt)


### Weird concern about these two packages:

For `install-rectangular-package` and `install-polar-package`
It's kind of weird that some methods are tagged with a list, 
and other methods are tagged without a list (like `'make-from-real-imag`).
I notice that things tagged with a list seem to be called through
`apply-generic`, while things tagged without a list seem to be called
through `get`. eg:

```rkt
(define (install-rectangular-package)
  ;; internal procedures
  (define (real-part z) (car z))
  (define (imag-part z) (cdr z))
  (define (make-from-real-imag x y) 
    (cons x y))
  (define (magnitude z)
    (sqrt (+ (square (real-part z))
             (square (imag-part z)))))
  (define (angle z)
    (atan (imag-part z) (real-part z)))
  (define (make-from-mag-ang r a)
    (cons (* r (cos a)) (* r (sin a))))
  ;; interface to the rest of the system
  (define (tag x) 
    (attach-tag 'rectangular x))
  (put 'real-part '(rectangular) real-part)
  (put 'imag-part '(rectangular) imag-part)
  (put 'magnitude '(rectangular) magnitude)
  (put 'angle '(rectangular) angle)
  (put 'make-from-real-imag 'rectangular
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'rectangular
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  'done)

(define (install-polar-package)
  ;; internal procedures
  (define (magnitude z) (car z))
  (define (angle z) (cdr z))
  (define (make-from-mag-ang r a) (cons r a))
  (define (real-part z)
    (* (magnitude z) (cos (angle z))))
  (define (imag-part z)
    (* (magnitude z) (sin (angle z))))
  (define (make-from-real-imag x y)
    (cons (sqrt (+ (square x) (square y)))
          (atan y x)))
  ;; interface to the rest of the system
  (define (tag x) (attach-tag 'polar x))
  (put 'real-part '(polar) real-part)
  (put 'imag-part '(polar) imag-part)
  (put 'magnitude '(polar) magnitude)
  (put 'angle '(polar) angle)
  (put 'make-from-real-imag 'polar
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'polar
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  'done)

(define (real-part z) 
  (apply-generic 'real-part z))
(define (imag-part z) 
  (apply-generic 'imag-part z))
(define (magnitude z) 
  (apply-generic 'magnitude z))
(define (angle z) 
  (apply-generic 'angle z))
(define (make-from-real-imag x y)
  ((get 'make-from-real-imag 
        'rectangular) 
   x y))
(define (make-from-mag-ang r a)
  ((get 'make-from-mag-ang 
        'polar) 
   r a))
```



### Introduction

Important functions: `put, get, apply-generic`.

Mutability hasn't been covered yet, so we can't really implement `put`.



### Exercises

##### Solution

#### Exercise 2.73

2.3.2 described a
program that performs symbolic differentiation:

```rkt
(define (deriv exp var)
  (cond ((number? exp) 0)
        ((variable? exp) 
         (if (same-variable? exp var) 1 0))
        ((sum? exp)
         (make-sum (deriv (addend exp) var)
                   (deriv (augend exp) var)))
        ((product? exp)
         (make-sum
           (make-product 
            (multiplier exp)
            (deriv (multiplicand exp) var))
           (make-product 
            (deriv (multiplier exp) var)
            (multiplicand exp))))
        ⟨@var{more rules can be added here}⟩
        (else (error "unknown expression type:
                      DERIV" exp))))
```

We can regard this program as performing a dispatch on the type of the
expression to be differentiated.  In this situation the ``type tag'' of the
datum is the algebraic operator symbol (such as `+`) and the operation
being performed is `deriv`.  We can transform this program into
data-directed style by rewriting the basic derivative procedure as

```rkt
(define (deriv exp var)
   (cond ((number? exp) 0)
         ((variable? exp) 
           (if (same-variable? exp var) 
               1 
               0))
         (else ((get 'deriv (operator exp)) 
                (operands exp) 
                var))))

(define (operator exp) (car exp))
(define (operands exp) (cdr exp))
```

**1.** Explain what was done above.  Why can't we assimilate the predicates
`number?` and `variable?` into the data-directed dispatch?

**2.** Write the procedures for derivatives of sums and products, and the auxiliary
code required to install them in the table used by the program above.

**3.** Choose any additional differentiation rule that you like, such as the one for
exponents (Exercise 2.56), and install it in this data-directed
system.

**4.** In this simple algebraic manipulator the type of an expression is the algebraic
operator that binds it together.  Suppose, however, we indexed the procedures
in the opposite way, so that the dispatch line in `deriv` looked like

```rkt
((get (operator exp) 'deriv) 
 (operands exp) var)
```


What corresponding changes to the derivative system are required?

##### Solution

**Part 1:** We can't assimilate the cases where it's a number or variable, because these aren't tagged data.

**Part 2 and part 3:** Note: I removed the keyword `operands` from
the function `deriv`, as this is more consistent with the code. 
I could have added the tag back everywhere `(let ((exp-tagged (cons '+ exp))) ...)`, but it's easier to just remove `operands`.

@src(code/ex2-73.rkt)

**Part 4:** We just have to switch the order of the tags,
it's trivial, here's the diff:
```
0a1
> 
91c92
<         (else ((get 'deriv (operator exp))
---
>         (else ((get (operator exp) 'deriv)
95c96
< (put 'deriv '+ 
---
> (put '+ 'deriv 
100c101
< (put 'deriv '* 
---
> (put '* 'deriv 
109c110
< (put 'deriv '**
---
> (put '** 'deriv 
```

#### Exercise 2.74

Insatiable Enterprises, Inc., is
a highly decentralized conglomerate company consisting of a large number of
independent divisions located all over the world.  The company's computer
facilities have just been interconnected by means of a clever
network-interfacing scheme that makes the entire network appear to any user to
be a single computer.  Insatiable's president, in her first attempt to exploit
the ability of the network to extract administrative information from division
files, is dismayed to discover that, although all the division files have been
implemented as data structures in Scheme, the particular data structure used
varies from division to division.  A meeting of division managers is hastily
called to search for a strategy to integrate the files that will satisfy
headquarters' needs while preserving the existing autonomy of the divisions.

Show how such a strategy can be implemented with data-directed programming.  As
an example, suppose that each division's personnel records consist of a single
file, which contains a set of records keyed on employees' names.  The structure
of the set varies from division to division.  Furthermore, each employee's
record is itself a set (structured differently from division to division) that
contains information keyed under identifiers such as `address` and
`salary`.  In particular:

**1.** Implement for headquarters a `get-record` procedure that retrieves a
specified employee's record from a specified personnel file.  The procedure
should be applicable to any division's file.  Explain how the individual
divisions' files should be structured.  In particular, what type information
must be supplied?

**2.** Implement for headquarters a `get-salary` procedure that returns the
salary information from a given employee's record from any division's personnel
file.  How should the record be structured in order to make this operation
work?

**3.** Implement for headquarters a `find-employee-record` procedure.  This
should search all the divisions' files for the record of a given employee and
return the record.  Assume that this procedure takes as arguments an employee's
name and a list of all the divisions' files.

**4.** When Insatiable takes over a new company, what changes must be made in order to
incorporate the new personnel information into the central system?

##### Solution

Kind of a weird problem, let's use 
`(define (lookup given-key records) ...)` from exercise 2.66.

1. The individual divisions' files need to have a tag to let us know what filetype we're dealing with. Then, inspired by the `lookup` function of question ch 2.66, we can use `((get 'get-record filetype) employee-name file-contents)`. This requires each division to implement and install a `get-record` function that accepts an employee name. Let's say it returns a record tagged with the division name. Let's be more precise to prepare for part 3:

```rkt 
;;Assume this returns false if no record exists.
(define (lookup-employee employee-name file)
  (let ((filetype (car file)) (file-contents (cdr file)))
    ((get 'get-record filetype) employee-name file-contents)))
```

2. For get-salary, we require each department implement a `get-salary` dispatchable function. Then we call `(apply-generic 'get-salary tagged-record)`.
3. Let's include a list of file contents. Each file is a list `(list filetype filecontents)`. 

```rkt
(define (find-employee-record employee-name tagged-files)
  (if (null? tagged-files) #f
    (let ((employee-record (lookup-employee employee-name (car tagged-files))))
      (if employee-record 
        employee-record
        (find-employee-record employee-name (cdr tagged-files))))))
```
4. To incorporate changes, we need to have people implement the `'get-record` 
and `get-salary` functions as defined earlier in the chapter.

#### Exercise 2.75

Implement the constructor
`make-from-mag-ang` in message-passing style.  This procedure should be
analogous to the `make-from-real-imag` procedure given above.

##### Solution

@src(code/ex2-75.rkt)

#### Exercise 2.76

As a large system with generic
operations evolves, new types of data objects or new operations may be needed.
For each of the three strategies---generic operations with explicit dispatch,
data-directed style, and message-passing-style---describe the changes that
must be made to a system in order to add new types or new operations.  Which
organization would be most appropriate for a system in which new types must
often be added?  Which would be most appropriate for a system in which new
operations must often be added?

##### Solution

**Generic operations with explicit dispatch:** This works well when 
we can be certain we don't have to add new types and operations.

**Data-directed:** Works extremely well when we have lot of different types, or have
functions that deal with arguments of many different types. So this would work best
when we have to add a bunch of different types. 

**Message-passing:** Makes adding new functions very easy. We still have the 
flexibility to add new types quite easily, but it might not be as explicit as the 
data directed approach. So message-passing would be preferable when 
new operations must often be added.

