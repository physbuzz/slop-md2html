
@toc


# Building the Query System from the Ground Up

I found section 4-4 incredibly difficult to read. This section is my supplement
to 4-4. Instead of taking the approach of describing the abstract ideas up-front
and leaving the concrete code to the end of the chapter, I instead try to 
make everything concrete from the get-go and build systems from scratch.

Still a WIP. But I imagine that what I'll have to do is that some pieces of 
the system will be fully-featured or are verbatim what is in the book. 
At other times it might make sense to build systems which are less general or
fail at certain edge cases. So hopefully I can make it clear which code blocks
are flawed or not fully featured.

I think it's natural to divide this into two sections: First, we cover the 
construction of a database system that handles simple and compound queries,
with `and` and `or`. After this, we deal with the topic of rules and
unification.

## 1. The Database System

### 1.1 Frames

A *frame* is an association list with keys `'(? variable)` and values 
representing the bound value of the variable. For example in the process
of matching the query `'(a b ?x)` to datum `'(a b c)`, 
we generate the frame `'(((? x) . c))`. Note that the symbol `?x` is expanded
into `'(? x)` by the procedures in `expand-question-mark` and `query-syntax-process` (4.4.4.7).

Running some examples (with the code in 4.4.4.8), we can get a feel for how things work. We define two frames by extending the empty frame `'()`.

```rkt
(define frame1 (extend '(? x) 'a '()))
(define frame2 (extend '(? y) 'b frame1))
```

Looking up behaves as expected:

```rkt
frame2
;; (((? y) . b) ((? x) . a))

(binding-in-frame '(? x) frame2)
;; ((? x) . a)

(binding-in-frame '(? y) frame2)
;; ((? y) . b)
```

and we note that we haven't done anything special to prevent inconsistent frame extensions! This has to be checked for elsewhere.
```rkt
(extend '(? x) 'b frame2)
;; (((? x) . b) ((? y) . b) ((? x) . a))
```

Note that extending a frame makes things *more* specific, because we specify
that the placeholder `'?x` has to be bound to a specific value. This means that
later on, the `and` operator will have a simple implementation because each
time we extend the frame in all possible ways we add more conditions on 
what matches we'll accept.

@src(code/4-4-simple-frame.rkt, collapsed)

### 1.2. Simple Pattern Matching

Next we consider the simple pattern matching algorithm. 
"Simple" means that we don't handle
`and`, `or`, `not`, or `'lisp-value` yet.

Our function `pattern-match` is going to take three arguments:
`pat`, `dat` and `frame` and is going to traverse the whole datum `dat` recursively. If we can satisfy the given pattern, then we'll return the correct frame extension. For example:
```rkt
(pattern-match '((? x) (? x) (? y) (? y))
               '(foo foo bar bar)
               '(((? x) . foo)))
;; (((? y) . bar) ((? x) . foo))

(pattern-match '((? x) (? x) (? y) (? y))
               '(bar bar bar bar)
               '(((? x) . foo)))
;; 'failed
```

@src(code/4-4-simple-pattern-match.rkt, collapsed)

The implementation is fairly straightforward.
`pattern-match` and `extend-if-consistent` are functions which call each other. 
`extend-if-consistent` is a helper function which actually does the symbol lookup and the 
extension to the frame. In order to determine if the pattern matching has failed or not, it calls 
`extend-if-consistent` with the pattern found by substitution from the database. 

To test understanding, I recommend trying to remember what the missing pattern `<...>` should be in the following code
snippet.

```rkt
(define (tagged-list? exp tag) (and (pair? exp) (eq? (car exp) tag)))
(define (var? exp) (tagged-list? exp '?))
(define (pattern-match pat dat frame)
  (cond ((eq? frame 'failed) 'failed)
        ((equal? pat dat) frame)
        ((var? pat) (extend-if-consistent pat dat frame))
        ((and (pair? pat) (pair? dat))
         (pattern-match <...>))
        (else 'failed)))
(define (extend-if-consistent var dat frame)
  (let ((binding (binding-in-frame var frame)))
    (if binding
        (pattern-match 
         (binding-value binding) dat frame)
        (extend var dat frame))))
```

**One weird thing:** I notice that in `extend-if-consistent`, we call pattern-match using a pattern which is the 
result of substituting user data. This means if our database contains malicious patterns like `'(? new-rule)` 
then we would start running checks based on user-provided rules! This is super funky, but whatever.

### 1.3. Building the database

For this section, we need to mash together code from section 4.4.4.3, 4.4.4.5, and 4.4.4.8. 
However, it's really all just bookkeeping. 

The new stuff is in 4.4.4.5. The book discusses that the indexing trick
is just so that if we have a pattern `(job ?a ?b)` this is never even 
checked against queries of the form `(address ?a ?b)`. 
It takes a lot of helper functions to make this easy, and in the code example below
I included all of the bookkeeping for the `rule` code even though it is not used.

Section 4.4.4.4 is skipped because it is not needed for simple or compound queries, or for database
construction or traversal. 

Finally, we already discussed the meat of section 4.4.4.3, `extend-if-consistent` and `pattern-match`. 
Two more bookkeeping functions are added here: 
`check-an-assertion` just wraps `pattern-match` so that it returns a singleton stream or the empty stream;
`find-assertions` just maps this across the database.

So, we define all of this code, we add a whole bunch of assertions...

```rkt
(define (build-database)
  (begin 
    (add-assertion! '(address (Bitdiddle Ben)
                              (Slumerville (Ridge Road) 10)))
    (add-assertion! '(job (Bitdiddle Ben) (computer wizard)))
    (add-assertion! '(salary (Bitdiddle Ben) 60000))
    ... ))
```

And finally, we run the code. Let's take the examples in exercise 4.55, and keep in mind that
the outputs are not going to be what is referred to as the "instantiated" query, we are just 
outputting the relevant list of frames. Also, keep in mind that we have to expand the symbols
`'?x` to the tagged list `'(? x)` by hand, since this is what our system expects.

```rkt
(build-database)
;; 'ok

(display-stream
  (find-assertions '(supervisor (? x) (Bitdiddle Ben)) '()))
;; (((? x) Tweakit Lem E))
;; (((? x) Fect Cy D))
;; (((? x) Hacker Alyssa P))

(display-stream
  (find-assertions '(job (? name) (accounting . (? type))) '()))
;; (((? type) scrivener) ((? name) Cratchet Robert))
;; (((? type) chief accountant) ((? name) Scrooge Eben))

(display-stream
  (find-assertions '(address (? name) (Slumerville . (? address))) '()))
;; (((? address) (Onion Square) 5) ((? name) Aull DeWitt))
;; (((? address) (Pine Tree Road) 80) ((? name) Reasoner Louis))
;; (((? address) (Ridge Road) 10) ((? name) Bitdiddle Ben))
```

@src(code/4-4-simple-database.rkt,collapsed)


### 1.4. Input-output-driver for simple queries

Next, we include all of the functions from 4.4.4.7. This is all trivial stuff and helper functions.
The interesting stuff forming the driver loop is in 4.4.4.1, and most of it is not necessary.

`qeval` provides a layer of indirection, so that it looks up the proper function using `get`. This will
be used later for rules and for compound queries, but not right now.

`simple-query` makes sure to append all possibilities from applying both assertions and rules, but if 
we only have assertions, it does nothing. I make sure to define a placeholder `apply-rules` that does nothing:

```rkt
(define (apply-rules query-pattern frame) the-empty-stream)
```

Next, `instantiate` is interesting. In the last section we noted that our output was in terms of frames, 
`instantiate` makes our output in terms of instantiated queries (with the variables replaced with the 
variable in each frame). 

Finally, the driver loop just dispatches things nicely, as well as expanding the question marks for us. 
Instead of a REPL, I define a `run-query` function that does basically the same thing as `query-driver-loop`.  

```rkt
(define (query-driver-loop) ...)
(define (instantiate exp frame unbound-var-handler) ...)
(define (qeval query frame-stream) ...)
(define (simple-query query-pattern frame-stream) ...)
```

Our code can then be run more simply. The only features we use are expanding the question marks automatically
and instantiating our outputs instead of listing frames, however because we have `qeval` which can dispatch
to more functions, and the call to `apply-rules` which can later be filled in, we have all the flexibility
we need. 
```rkt
(build-database)

(display-line "Query (supervisor ?x (Bitdiddle Ben)):")
(display-stream
 (run-query '(supervisor ?x (Bitdiddle Ben))))
(newline)
;; (supervisor (Tweakit Lem E) (Bitdiddle Ben))
;; (supervisor (Fect Cy D) (Bitdiddle Ben))
;; (supervisor (Hacker Alyssa P) (Bitdiddle Ben))

(display-line "Query (job ?name (accounting . ?type)):")
(display-stream
 (run-query '(job ?name (accounting . ?type))))
(newline)
;; (job (Cratchet Robert) (accounting scrivener))
;; (job (Scrooge Eben) (accounting chief accountant))

(display-line "Query (address ?name (Slumerville . ?address)):")
(display-stream
 (run-query '(address ?name (Slumerville . ?address))))
(newline)
;; (address (Aull DeWitt) (Slumerville (Onion Square) 5))
;; (address (Reasoner Louis) (Slumerville (Pine Tree Road) 80))
;; (address (Bitdiddle Ben) (Slumerville (Ridge Road) 10))
```

@src(code/4-4-simple-driver.rkt,collapsed)


### 1.5. Input-output-driver for compound queries
@src(code/4-4-compound-queries.rkt,collapsed)

## 2. Rules and Unification

### 2.1 Unification (Extending Simple Pattern Matching)

We defined `(pattern-match pat dat frame)` in section 1.2 of this note.
Now, we allow `dat` to also be a pattern. So our new function will be
more complicated but a bit more symmetric, `(unify-match p1 p2 frame)`.



If we imagine performing a match where one of `p1` or `p2` contain no
pattern variables, then the behavior is exactly like `pattern-match`.
Therefore, we want the following behavior:

```rkt
(display 
  (unify-match '(+ (? x) (* 5 4)) '(+ 3 (* 5 4)) '()))
;; (((? x) . 3))
(display 
  (unify-match '(+ 3 (* 5 4)) '(+ 3 (* 5 (? w))) '()))
;; (((? w) . 4))
```

It's very easy to write this in a way such that the generic case 
with non-conflicting patterns on both sides is handled correctly. Just like
`query-pattern`, we do a depth first search from left-to-right.

```rkt
(display 
  (unify-match '(+ (? x) (* (? y) 4)) '(+ 3 (* 5 (? w))) '()))
;; (((? w) . 4) ((? y) . 5) ((? x) . 3))
```

Now, the slightly clever stuff, we also handle cases where 
the substitution values are themselves variables.

```rkt
(display 
  (unify-match '(+ (? x) (* (? y) 4)) 
               '(+ 3 (* (? z) (? w))) '()))
;; (((? w) . 4) ((? y) ? z) ((? x) . 3))

(display 
  (unify-match '(+ (? x) (* (? y) 4)) 
               '(+ 3 (* (? y) (? w))) '()))
;; (((? w) . 4) ((? x) . 3))

(display 
  (unify-match '(+ (? x) (* 5 (? y))) 
               '(+ (f (? y)) (* 5 4)) '()))
;; (((? y) . 4) ((? x) f (? y)))
```

In the third example, note that the `instantiate` function handles the rule
substitution properly.

There are cases where the left-to-right 

```
(display 
  (unify-match '(+ (f (? x)) (* 5 (? x))) 
               '(+ (? y) (* 5 4)) '()))
;; (((? x) . 4) ((? y) f (? x)))

(display 
  (unify-match '(+ (? x) (* (? y) (? z))) 
               '(+ (? z) (* (? x) (? y))) '()))
;; (((? y) ? z) ((? x) ? z))
```



The goal of `unify-match` is to find a frame
extension that makes both patterns equal to each other,  


`(define 


###

###

# My Misconceptions

## "The output of a Query"
In 4.4.1, we give the example of the query:
```rkt
(and (job ?person (computer programmer))
     (address ?person ?where))
```

giving the output 
```rkt
(and (job (Hacker Alyssa P) 
          (computer programmer))
     (address (Hacker Alyssa P) 
              (Cambridge (Mass Ave) 78)))

(and (job (Fect Cy D) (computer programmer))
     (address (Fect Cy D) 
              (Cambridge (Ames Street) 3)))
```

The book also says "the output of the query is a stream of frames." 
You might think this means that our two `(and ...)` statements are the
two elements in the stream of frames, but this is incorrect! In my opinion
the book's phrasing is highly misleading here, the stream of frames which is
relevant to our query has two elements, which are:

```rkt
'(((? person) . (Hacker Alyssa P)) ((? where) . (Cambridge (Mass Ave) 78)))
'(((? person) . (Fect Cy D)) ((? where) . (Cambridge (Ames Street) 3)))
```

Later (in 4.4.4.1) we `instantiate` those frames using the input query expression, the 
frame, and a function to handle unbound variables:
```rkt
(define (instantiate 
         exp frame unbound-var-handler) ...)
```





