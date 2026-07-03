<div class="nav">
    <span class="activenav"><a href="notes-ch4-2.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="activenav"><a href="notes-ch4-4.html">Next →</a></span>
</div>

[HTML Book Chapter 4.3 Link](https://sarabander.github.io/sicp/html/4_002e3.xhtml#g_t4_002e3)

@toc

## Section 4.3

### Notes

### Exercises

#### Exercise 4.35

Write a procedure
`an-integer-between` that returns an integer between two given bounds.
This can be used to implement a procedure that finds Pythagorean triples, i.e.,
triples of integers ${(i, j, k)$} between the given bounds such that
${i \le j$} and ${i^2 + j^2 = k^2$}, as follows:

```rkt
(define (a-pythagorean-triple-between low high)
  (let ((i (an-integer-between low high)))
    (let ((j (an-integer-between i high)))
      (let ((k (an-integer-between j high)))
        (require (= (+ (* i i) (* j j)) 
                    (* k k)))
        (list i j k)))))
```

##### Solution

#### Exercise 4.36

Exercise 3.69 discussed how
to generate the stream of *all* Pythagorean triples, with no upper bound
on the size of the integers to be searched.  Explain why simply replacing
`an-integer-between` by `an-integer-starting-from` in the procedure
in Exercise 4.35 is not an adequate way to generate arbit@-rary Py@-tha@-go@-rean
triples.  Write a procedure that actually will accomplish this.  (That is,
write a procedure for which repeatedly typing `try-again` would in
principle eventually generate all Py@-tha@-go@-rean triples.)

##### Solution

#### Exercise 4.37

Ben Bitdiddle claims that the
following method for generating Pythagorean triples is more efficient than the
one in Exercise 4.35.  Is he correct?  (Hint: Consider the number of
possibilities that must be explored.)

```rkt
(define (a-pythagorean-triple-between low high)
  (let ((i (an-integer-between low high))
        (hsq (* high high)))
    (let ((j (an-integer-between i high)))
      (let ((ksq (+ (* i i) (* j j))))
        (require (>= hsq ksq))
        (let ((k (sqrt ksq)))
          (require (integer? k))
          (list i j k))))))
```

##### Solution

#### Exercise 4.38

Modify the multiple-dwelling
procedure to omit the requirement that Smith and Fletcher do not live on
adjacent floors.  How many solutions are there to this modified puzzle?

##### Solution

#### Exercise 4.39

Does the order of the
restrictions in the multiple-dwelling procedure affect the answer? Does it
affect the time to find an answer?  If you think it matters, demonstrate a
faster program obtained from the given one by reordering the restrictions.  If
you think it does not matter, argue your case.

##### Solution

#### Exercise 4.40

In the multiple dwelling problem,
how many sets of assignments are there of people to floors, both before and
after the requirement that floor assignments be distinct?  It is very
inefficient to generate all possible assignments of people to floors and then
leave it to backtracking to eliminate them.  For example, most of the
restrictions depend on only one or two of the person-floor variables, and can
thus be imposed before floors have been selected for all the people.  Write and
demonstrate a much more efficient nondeterministic procedure that solves this
problem based upon generating only those possibilities that are not already
ruled out by previous restrictions.  (Hint: This will require a nest of
`let` expressions.)

##### Solution

#### Exercise 4.41

Write an ordinary Scheme program
to solve the multiple dwelling puzzle.

##### Solution

#### Exercise 4.42

Solve the following ``Liars''
puzzle (from Phillips 1934):

Five schoolgirls sat for an examination.  Their parents---so they
thought---showed an undue degree of interest in the result.  They therefore
agreed that, in writing home about the examination, each girl should make one
true statement and one untrue one.  The following are the relevant passages
from their letters:

@itemize @bullet

@item
Betty: ``Kitty was second in the examination.  I was only third.''

@item
Ethel: ``You'll be glad to hear that I was on top.  Joan was second.''

@item
Joan: ``I was third, and poor old Ethel was bottom.''

@item
Kitty: ``I came out second.  Mary was only fourth.''

@item
Mary: ``I was fourth.  Top place was taken by Betty.''



What in fact was the order in which the five girls were placed?

##### Solution

#### Exercise 4.43

Use the `amb` evaluator to
solve the following puzzle:

@quotation
Mary Ann Moore's father has a yacht and so has each of his four friends:
Colonel Downing, Mr. Hall, Sir Barnacle Hood, and Dr.  Parker.  Each of the
five also has one daughter and each has named his yacht after a daughter of one
of the others.  Sir Barnacle's yacht is the Gabrielle, Mr. Moore owns the
Lorna; Mr. Hall the Rosalind.  The Melissa, owned by Colonel Downing, is named
after Sir Barnacle's daughter.  Gabrielle's father owns the yacht that is named
after Dr.  Parker's daughter.  Who is Lorna's father?

##### Solution

#### Exercise 4.44

Exercise 2.42 described the
``eight-queens puzzle'' of placing queens on a chessboard so that no two attack
each other.  Write a nondeterministic program to solve this puzzle.

##### Solution

#### Exercise 4.45

With the grammar given above, the
following sentence can be parsed in five different ways: ``The professor
lectures to the student in the class with the cat.''  Give the five parses and
explain the differences in shades of meaning among them.

##### Solution

#### Exercise 4.46

The evaluators in 
4.1 and 4.2 do not determine what order operands are evaluated in.
We will see that the `amb` evaluator evaluates them from left to right.
Explain why our parsing program wouldn't work if the operands were evaluated in
some other order.

##### Solution

#### Exercise 4.47

Louis Reasoner suggests that,
since a verb phrase is either a verb or a verb phrase followed by a
prepositional phrase, it would be much more straightforward to define the
procedure `parse-verb-phrase` as follows (and similarly for noun phrases):

```rkt
(define (parse-verb-phrase)
  (amb (parse-word verbs)
       (list 
        'verb-phrase
        (parse-verb-phrase)
        (parse-prepositional-phrase))))
```

Does this work?  Does the program's behavior change if we interchange the order
of expressions in the `amb`?

##### Solution

#### Exercise 4.48

Extend the grammar given above to
handle more complex sentences.  For example, you could extend noun phrases and
verb phrases to include adjectives and adverbs, or you could handle compound
sentences.

##### Solution

#### Exercise 4.49

Alyssa P. Hacker is more
interested in generating interesting sentences than in parsing them.  She
reasons that by simply changing the procedure `parse-word` so that it
ignores the ``input sentence'' and instead always succeeds and generates an
appropriate word, we can use the programs we had built for parsing to do
generation instead.  Implement Alyssa's idea, and show the first half-dozen or
so sentences generated.

##### Solution

#### Exercise 4.50

Implement a new special form
`ramb` that is like `amb` except that it searches alternatives in a
random order, rather than from left to right.  Show how this can help with
Alyssa's problem in Exercise 4.49.

##### Solution

#### Exercise 4.51

Implement a new kind of
assignment called `permanent-set!` that is not undone upon failure.  For
example, we can choose two distinct elements from a list and count the number
of trials required to make a successful choice as follows:

```rkt
(define count 0)
(let ((x (an-element-of '(a b c)))
      (y (an-element-of '(a b c))))
  (permanent-set! count (+ count 1))
  (require (not (eq? x y)))
  (list x y count))

;;; Starting a new problem
;;; Amb-Eval value:
(a b 2)

;;; Amb-Eval input:
try-again

;;; Amb-Eval value:
(a c 3)
```

What values would have been displayed if we had used `set!` here
rather than `permanent-set!`?

##### Solution

#### Exercise 4.52

Implement a new construct called
`if-fail` that permits the user to catch the failure of an expression.
`If-fail` takes two expressions.  It evaluates the first expression as
usual and returns as usual if the evaluation succeeds.  If the evaluation
fails, however, the value of the second expression is returned, as in the
following example:

```rkt
;;; Amb-Eval input:
(if-fail 
 (let ((x (an-element-of '(1 3 5))))
   (require (even? x))
   x)
 'all-odd)

;;; Starting a new problem
;;; Amb-Eval value:
all-odd

;;; Amb-Eval input:
(if-fail
 (let ((x (an-element-of '(1 3 5 8))))
   (require (even? x))
   x)
 'all-odd)

;;; Starting a new problem
;;; Amb-Eval value:
8
```

##### Solution

#### Exercise 4.53

With `permanent-set!` as
described in Exercise 4.51 and `if-fail` as in Exercise 4.52,
what will be the result of evaluating

```rkt
(let ((pairs '()))
  (if-fail 
   (let ((p (prime-sum-pair 
             '(1 3 5 8) 
             '(20 35 110))))
     (permanent-set! pairs 
                     (cons p pairs))
     (amb))
   pairs))
```

##### Solution

#### Exercise 4.54

If we had not realized that
`require` could be implemented as an ordinary procedure that uses
`amb`, to be defined by the user as part of a nondeterministic program, we
would have had to implement it as a special form.  This would require syntax
procedures

```rkt
(define (require? exp) 
  (tagged-list? exp 'require))

(define (require-predicate exp) 
  (cadr exp))
```


and a new clause in the dispatch in `analyze`

```rkt
((require? exp) (analyze-require exp))
```


as well the procedure `analyze-require` that handles `require`
expressions.  Complete the following definition of `analyze-require`.

```rkt
(define (analyze-require exp)
  (let ((pproc (analyze 
                (require-predicate exp))))
    (lambda (env succeed fail)
      (pproc env
             (lambda (pred-value fail2)
               (if ⟨??⟩
                   ⟨??⟩
                   (succeed 'ok fail2)))
             fail))))
```

##### Solution

