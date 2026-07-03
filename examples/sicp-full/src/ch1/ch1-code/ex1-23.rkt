#lang sicp

(define (smallest-divisor n)
  (find-divisor n 2))

(define (find-divisor n test-divisor)
  (cond ((> (* test-divisor test-divisor) n) 
         n)
        ((divides? test-divisor n) 
         test-divisor)
        (else (find-divisor 
               n 
               (nextdiv test-divisor)))))

(define (divides? a b)
  (= (remainder b a) 0))

(define (prime? n)
  (= n (smallest-divisor n)))

(define (nextdiv test-divisor)
  (if (= test-divisor 2) 
    3 
    (+ test-divisor 2)))

(define (timed-prime-test n start-time)
  (if (prime? n)
    (begin 
      (display n)
      (display " : ")
      (display (- (runtime) start-time))
      (display "ms")
      (newline)
      #t)
    #f))

(define (primes-larger-than n k-primes)
  (if (not (= k-primes 0))
    (if (timed-prime-test n (runtime)) 
      (primes-larger-than (+ n 1) (- k-primes 1))
      (primes-larger-than (+ n 1) k-primes))))

(primes-larger-than 100000000 3)
(primes-larger-than 1000000000 3)
(primes-larger-than 10000000000 3)
