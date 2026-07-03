<div class="nav">
    <span class="activenav"><a href="notes-ch5-2.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch5-4.html">Next →</a></span>
</div>

[HTML Book Chapter 5.3 Link](https://sarabander.github.io/sicp/html/5_002e3.xhtml#g_t5_002e3)

@toc

## Section 5.3

### Notes

### Exercises

#### Exercise 5.20

Draw the box-and-pointer
representation and the memory-vector representation (as in Figure 5.14)
of the list structure produced by

```rkt
(define x (cons 1 2))
(define y (list x x))
```


with the `free` pointer initially `p1`.  What is the final value of
`free`?  What pointers represent the values of `x` and `y`?

##### Solution

#### Exercise 5.21

Implement register machines for
the following procedures.  Assume that the list-structure memory operations are
available as machine primitives.

**1.** Recursive `count-leaves`:

```rkt
(define (count-leaves tree)
  (cond ((null? tree) 0)
        ((not (pair? tree)) 1)
        (else 
         (+ (count-leaves (car tree))
            (count-leaves (cdr tree))))))
```

**2.** Recursive `count-leaves` with explicit counter:

```rkt
(define (count-leaves tree)
  (define (count-iter tree n)
    (cond ((null? tree) n)
          ((not (pair? tree)) (+ n 1))
          (else 
           (count-iter 
            (cdr tree)
            (count-iter (car tree) 
                        n)))))
  (count-iter tree 0))
```



##### Solution

#### Exercise 5.22

Exercise 3.12 of 
3.3.1 presented an `append` procedure that appends two lists to form
a new list and an `append!` procedure that splices two lists together.
Design a register machine to implement each of these procedures.  Assume that
the list-structure memory operations are available as primitive operations.

##### Solution

