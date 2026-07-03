<div class="nav">
    <span class="activenav"><a href="notes-ch5-4.html">← Previous</a></span>
    <span class="activenav"><a href="../index.html">↑ Up</a></span>
    <span class="inactivenav">Next →</span>
</div>

[HTML Book Chapter 5.5 Link](https://sarabander.github.io/sicp/html/5_002e5.xhtml#g_t5_002e5)

@toc

## Section 3.1

### Notes

### Exercises

#### Exercise 5.31

In evaluating a procedure
application, the explicit-control evaluator always saves and restores the
`env` register around the evaluation of the operator, saves and restores
`env` around the evaluation of each operand (except the final one), saves
and restores `argl` around the evaluation of each operand, and saves and
restores `proc` around the evaluation of the operand sequence.  For each
of the following combinations, say which of these `save` and
`restore` operations are superfluous and thus could be eliminated by the
compiler's `preserving` mechanism:

```rkt
(f 'x 'y)
((f) 'x 'y)
(f (g 'x) y)
(f (g 'x) 'y)
```

##### Solution

#### Exercise 5.32

Using the `preserving`
mechanism, the compiler will avoid saving and restoring `env` around the
evaluation of the operator of a combination in the case where the operator is a
symbol.  We could also build such optimizations into the evaluator.  Indeed,
the explicit-control evaluator of 5.4 already performs a similar
optimization, by treating combinations with no operands as a special case.

**1.** Extend the explicit-control evaluator to recognize as a separate class of
expressions combinations whose operator is a symbol, and to take advantage of
this fact in evaluating such expressions.

**2.** Alyssa P. Hacker suggests that by extending the evaluator to recognize more and
more special cases we could incorporate all the compiler's optimizations, and
that this would eliminate the advantage of compilation altogether.  What do you
think of this idea?



##### Solution

#### Exercise 5.33

Consider the following definition
of a factorial procedure, which is slightly different from the one given above:

```rkt
(define (factorial-alt n)
  (if (= n 1)
      1
      (* n (factorial-alt (- n 1)))))
```

Compile this procedure and compare the resulting code with that produced for
`factorial`.  Explain any differences you find.  Does either program
execute more efficiently than the other?

##### Solution

#### Exercise 5.34

Compile the iterative factorial
procedure

```rkt
(define (factorial n)
  (define (iter product counter)
    (if (> counter n)
        product
        (iter (* counter product)
              (+ counter 1))))
  (iter 1 1))
```

Annotate the resulting code, showing the essential difference between the code
for iterative and recursive versions of `factorial` that makes one process
build up stack space and the other run in constant stack space.

##### Solution

#### Exercise 5.35

What expression was compiled to
produce the code shown in Figure 5.18?

##### Solution

#### Exercise 5.36

What order of evaluation does our
compiler produce for operands of a combination?  Is it left-to-right,
right-to-left, or some other order?  Where in the compiler is this order
determined?  Modify the compiler so that it produces some other order of
evaluation.  (See the discussion of order of evaluation for the
explicit-control evaluator in 5.4.1.)  How does changing the
order of operand evaluation affect the efficiency of the code that constructs
the argument list?

##### Solution

#### Exercise 5.37

One way to understand the
compiler's `preserving` mechanism for optimizing stack usage is to see
what extra operations would be generated if we did not use this idea.  Modify
`preserving` so that it always generates the `save` and
`restore` operations.  Compile some simple expressions and identify the
unnecessary stack operations that are generated.  Compare the code to that
generated with the `preserving` mechanism intact.

##### Solution

#### Exercise 5.38

Our compiler is clever about
avoiding unnecessary stack operations, but it is not clever at all when it
comes to compiling calls to the primitive procedures of the language in terms
of the primitive operations supplied by the machine.  For example, consider how
much code is compiled to compute `(+ a 1)`: The code sets up an argument
list in `argl`, puts the primitive addition procedure (which it finds by
looking up the symbol `+` in the environment) into `proc`, and tests
whether the procedure is primitive or compound.  The compiler always generates
code to perform the test, as well as code for primitive and compound branches
(only one of which will be executed).  We have not shown the part of the
controller that implements primitives, but we presume that these instructions
make use of primitive arithmetic operations in the machine's data paths.
Consider how much less code would be generated if the compiler could
open-code primitives---that is, if it could generate code to directly
use these primitive machine operations.  The expression `(+ a 1)` might be
compiled into something as simple as

```rkt
(assign val (op lookup-variable-value) 
            (const a) 
            (reg env))
(assign val (op +)
            (reg val)
            (const 1))
```

In this exercise we will extend our compiler to support open coding of selected
primitives.  Special-purpose code will be generated for calls to these
primitive procedures instead of the general procedure-application code.  In
order to support this, we will augment our machine with special argument
registers `arg1` and `arg2`.  The primitive arithmetic operations of
the machine will take their inputs from `arg1` and `arg2`. The
results may be put into `val`, `arg1`, or `arg2`.

The compiler must be able to recognize the application of an open-coded
primitive in the source program.  We will augment the dispatch in the
`compile` procedure to recognize the names of these primitives in addition
to the reserved words (the special forms) it currently
recognizes. For each special
form our compiler has a code generator.  In this exercise we will construct a
family of code generators for the open-coded primitives.

**1.** The open-coded primitives, unlike the special forms, all need their operands
evaluated.  Write a code generator `spread-arguments` for use by all the
open-coding code generators.  `Spread-arguments` should take an operand
list and compile the given operands targeted to successive argument registers.
Note that an operand may contain a call to an open-coded primitive, so argument
registers will have to be preserved during operand evaluation.

**2.** For each of the primitive procedures `=`, `*`, `-`, and
`+`, write a code generator that takes a combination with that operator,
together with a target and a linkage descriptor, and produces code to spread
the arguments into the registers and then perform the operation targeted to the
given target with the given linkage.  You need only handle expressions with two
operands.  Make `compile` dispatch to these code generators.

**3.** Try your new compiler on the `factorial` example.  Compare the resulting
code with the result produced without open coding.

**4.** Extend your code generators for `+` and `*` so that they can handle
expressions with arbitrary numbers of operands.  An expression with more than
two operands will have to be compiled into a sequence of operations, each with
only two inputs.



##### Solution

#### Exercise 5.39

Write a procedure
`lexical-address-lookup` that implements the new lookup operation.  It
should take two arguments---a lexical address and a run-time environment---and
return the value of the variable stored at the specified lexical address.
`Lexical-address-lookup` should signal an error if the value of the
variable is the symbol `*unassigned*`. Also write a procedure
`lexical-address-set!` that implements the operation that changes the
value of the variable at a specified lexical address.

##### Solution

#### Exercise 5.40

Modify the compiler to maintain
the compile-time environment as described above.  That is, add a
compile-time-environment argument to `compile` and the various code
generators, and extend it in `compile-lambda-body`.

##### Solution

#### Exercise 5.41

Write a procedure
`find-variable` that takes as arguments a variable and a compile-time
environment and returns the lexical address of the variable with respect to
that environment.  For example, in the program fragment that is shown above,
the compile-time environment during the compilation of expression `⟨`@var{e1}`⟩` is
`((y z) (a b c d e) (x y))`.  `Find-variable` should produce

```rkt
(find-variable 
 'c '((y z) (a b c d e) (x y)))
(1 2)

(find-variable 
 'x '((y z) (a b c d e) (x y)))
(2 0)

(find-variable 
 'w '((y z) (a b c d e) (x y)))
not-found
```

##### Solution

#### Exercise 5.42

Using `find-variable` from
Exercise 5.41, rewrite `compile-variable` and
`compile-assignment` to output lexical-address instructions.  In cases
where `find-variable` returns `not-found` (that is, where the
variable is not in the compile-time environment), you should have the code
generators use the evaluator operations, as before, to search for the binding.
(The only place a variable that is not found at compile time can be is in the
global environment, which is part of the run-time environment but is not part
of the compile-time environment.  Thus, if you wish, you may have the evaluator operations look
directly in the global environment, which can be obtained with the operation
`(op get-global-environment)`, instead of having them search the whole
run-time environment found in `env`.)  Test the modified compiler on a few
simple cases, such as the nested `lambda` combination at the beginning of
this section.

##### Solution

#### Exercise 5.43

We argued in 4.1.6
that internal definitions for block structure should not be considered ``real''
`define`s.  Rather, a procedure body should be interpreted as if the
internal variables being defined were installed as ordinary `lambda`
variables initialized to their correct values using `set!`.  
4.1.6 and Exercise 4.16 showed how to modify the metacircular
interpreter to accomplish this by scanning out internal definitions.  Modify
the compiler to perform the same transformation before it compiles a procedure
body.

##### Solution

#### Exercise 5.44

In this section we have focused
on the use of the compile-time environment to produce lexical addresses.  But
there are other uses for compile-time environments.  For instance, in
Exercise 5.38 we increased the efficiency of compiled code by open-coding
primitive procedures.  Our implementation treated the names of open-coded
procedures as reserved words.  If a program were to rebind such a name, the
mechanism described in Exercise 5.38 would still open-code it as a
primitive, ignoring the new binding.  For example, consider the procedure

```rkt
(lambda (+ * a b x y)
  (+ (* a x) (* b y)))
```


which computes a linear combination of `x` and `y`.  We might call it
with arguments `+matrix`, `*matrix`, and four matrices, but the
open-coding compiler would still open-code the `+` and the `*` in
`(+ (* a x) (* b y))` as primitive `+` and `*`.  Modify the
open-coding compiler to consult the compile-time environment in order to
compile the correct code for expressions involving the names of primitive
procedures.  (The code will work correctly as long as the program does not
`define` or `set!` these names.)

##### Solution

#### Exercise 5.45

By comparing the stack operations
used by compiled code to the stack operations used by the evaluator for the
same computation, we can determine the extent to which the compiler optimizes
use of the stack, both in speed (reducing the total number of stack operations)
and in space (reducing the maximum stack depth).  Comparing this optimized
stack use to the performance of a special-purpose machine for the same
computation gives some indication of the quality of the compiler.

**1.** Exercise 5.27 asked you to determine, as a function of $n$, the number
of pushes and the maximum stack depth needed by the evaluator to compute ${n!$}
using the recursive factorial procedure given above.  Exercise 5.14 asked
you to do the same measurements for the special-purpose factorial machine shown
in Figure 5.11. Now perform the same analysis using the compiled
`factorial` procedure.

Take the ratio of the number of pushes in the compiled version to the number of
pushes in the interpreted version, and do the same for the maximum stack depth.
Since the number of operations and the stack depth used to compute ${n!$}  are
linear in $n$, these ratios should approach constants as $n$ becomes large.
What are these constants?  Similarly, find the ratios of the stack usage in the
special-purpose machine to the usage in the interpreted version.

Compare the ratios for special-purpose versus interpreted code to the ratios
for compiled versus interpreted code.  You should find that the special-purpose
machine does much better than the compiled code, since the hand-tailored
controller code should be much better than what is produced by our rudimentary
general-purpose compiler.

**2.** Can you suggest improvements to the compiler that would help it generate code
that would come closer in performance to the hand-tailored version?



##### Solution

#### Exercise 5.46

Carry out an analysis like the
one in Exercise 5.45 to determine the effectiveness of compiling the
tree-recursive Fibonacci procedure

```rkt
(define (fib n)
  (if (< n 2)
      n
      (+ (fib (- n 1)) (fib (- n 2)))))
```


compared to the effectiveness of using the special-purpose Fibonacci machine of
Figure 5.12.  (For measurement of the interpreted performance, see
Exercise 5.29.)  For Fibonacci, the time resource used is not linear in
${n;$} hence the ratios of stack operations will not approach a limiting value
that is independent of $n$.

##### Solution

#### Exercise 5.47

This section described how to
modify the explicit-control evaluator so that interpreted code can call
compiled procedures.  Show how to modify the compiler so that compiled
procedures can call not only primitive procedures and compiled procedures, but
interpreted procedures as well.  This requires modifying
`compile-procedure-call` to handle the case of compound (interpreted)
procedures.  Be sure to handle all the same `target` and `linkage`
combinations as in `compile-proc-appl`.  To do the actual procedure
application, the code needs to jump to the evaluator's `compound-apply`
entry point.  This label cannot be directly referenced in object code (since
the assembler requires that all labels referenced by the code it is assembling
be defined there), so we will add a register called `compapp` to the
evaluator machine to hold this entry point, and add an instruction to
initialize it:

```rkt
(assign compapp (label compound-apply))
  @r{;; branches if `flag` is set:}
  (branch (label external-entry))
read-eval-print-loop @r{…}
```

To test your code, start by defining a procedure `f` that calls a
procedure `g`.  Use `compile-and-go` to compile the definition of
`f` and start the evaluator.  Now, typing at the evaluator, define
`g` and try to call `f`.

##### Solution

#### Exercise 5.48

The `compile-and-go`
interface implemented in this section is awkward, since the compiler can be
called only once (when the evaluator machine is started).  Augment the
compiler-interpreter interface by providing a `compile-and-run` primitive
that can be called from within the explicit-control evaluator as follows:

```rkt
;;; EC-Eval input:
(compile-and-run
 '(define (factorial n)
    (if (= n 1)
        1
        (* (factorial (- n 1)) n))))

;;; EC-Eval value:
ok

;;; EC-Eval input:
(factorial 5)

;;; EC-Eval value:
120
```

##### Solution

#### Exercise 5.49

As an alternative to using the
explicit-control evaluator's read-eval-print loop, design a register machine
that performs a read-compile-execute-print loop.  That is, the machine should
run a loop that reads an expression, compiles it, assembles and executes the
resulting code, and prints the result.  This is easy to run in our simulated
setup, since we can arrange to call the procedures `compile` and
`assemble` as ``register-machine operations.''

##### Solution

#### Exercise 5.50

Use the compiler to compile the
metacircular evaluator of 4.1 and run this program using the
register-machine simulator.  (To compile more than one definition at a time,
you can package the definitions in a `begin`.)  The resulting interpreter
will run very slowly because of the multiple levels of interpretation, but
getting all the details to work is an instructive exercise.

##### Solution

#### Exercise 5.51

Develop a rudimentary
implementation of Scheme in C (or some other low-level language of your choice)
by translating the explicit-control evaluator of 5.4 into C.  In
order to run this code you will need to also provide appropriate
storage-allocation routines and other run-time support.

##### Solution

#### Exercise 5.52

As a counterpoint to 
Exercise 5.51, modify the compiler so that it compiles Scheme procedures
into sequences of C instructions.  Compile the metacircular evaluator of
4.1 to produce a Scheme interpreter written in C.

##### Solution

