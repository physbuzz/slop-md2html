<div class="nav">
    <span class="activenav"><a href="../ch4/notes-ch4-4.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch5-2.html">Next →</a></span>
</div>

[HTML Book Chapter 5.1 Link](https://sarabander.github.io/sicp/html/5_002e1.xhtml#g_t5_002e1)

@toc

## Section 5.1

### Notes

### Exercises

#### Exercise 5.1

Design a register machine to
compute factorials using the iterative algorithm specified by the following
procedure.  Draw data-path and controller diagrams for this machine.

```rkt
(define (factorial n)
  (define (iter product counter)
    (if (> counter n)
        product
        (iter (* counter product)
              (+ counter 1))))
  (iter 1 1))
```

#### Exercise 5.2

Use the register-machine language
to describe the iterative factorial machine of Exercise 5.1.

#### Exercise 5.3

Design a machine to compute square
roots using Newton's method, as described in Sec.1.1.7,,1.1.7:

```rkt
(define (sqrt x)
  (define (good-enough? guess)
    (< (abs (- (square guess) x)) 0.001))
  (define (improve guess)
    (average guess (/ x guess)))
  (define (sqrt-iter guess)
    (if (good-enough? guess)
        guess
        (sqrt-iter (improve guess))))
  (sqrt-iter 1.0))
```

Begin by assuming that `good-enough?` and `improve` operations are
available as primitives.  Then show how to expand these in terms of arithmetic
operations.  Describe each version of the `sqrt` machine design by drawing
a data-path diagram and writing a controller definition in the register-machine
language.

#### Exercise 5.4

Specify register machines that
implement each of the following procedures.  For each machine, write a
controller instruction sequence and draw a diagram showing the data paths.

**1.** Recursive exponentiation:

```rkt
(define (expt b n)
  (if (= n 0)
      1
      (* b (expt b (- n 1)))))
```

**2.** Iterative exponentiation:

```rkt
(define (expt b n)
  (define (expt-iter counter product)
    (if (= counter 0)
        product
        (expt-iter (- counter 1)
                   (* b product))))
  (expt-iter n 1))
```



#### Exercise 5.5

Hand-simulate the factorial and
Fibonacci machines, using some nontrivial input (requiring execution of at
least one recursive call).  Show the contents of the stack at each significant
point in the execution.

#### Exercise 5.6

Ben Bitdiddle observes that the
Fibonacci machine's controller sequence has an extra `save` and an extra
`restore`, which can be removed to make a faster machine.  Where are these
instructions?

