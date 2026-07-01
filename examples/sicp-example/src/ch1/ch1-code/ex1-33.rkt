#lang sicp

(define (filtered-accumulate 
           combiner filter? null-value term a next b)
  (if (> a b)
       null-value
       (filtered-accumulate combiner 
                            filter?
                            (if (filter? a) 
                              (combiner null-value (term a))
                              null-value)
                            term
                            (next a)
                            next
                            b)))

(define (smallest-divisor n)
  (find-divisor n 2))
(define (square n) (* n n))
(define (find-divisor n test-divisor)
  (cond ((> (square test-divisor) n) 
         n)
        ((divides? test-divisor n) 
         test-divisor)
        (else (find-divisor 
               n 
               (+ test-divisor 1)))))
(define (divides? a b)
  (= (remainder b a) 0))
(define (prime? n)
  (= n (smallest-divisor n)))
(define (ssquare-prime n)
  (filtered-accumulate + prime? 0 square 2 add-one n))

(define (gcd a b)
  (if (= b 0)
      a
      (gcd b (remainder a b))))
(define (id n) n)
(define (add-one n) (+ n 1))
(define (coprime-prod n)
  (define (coprime? a)
    (= 1 (gcd a n)))
  (filtered-accumulate * coprime? 1 id 1 add-one n))

(define (print-seq func a b)
  (cond ((> a b) (display ""))
        ((= a b) (display (func a)))
        (else (display (func a))
              (display ", ")
              (print-seq func (+ a 1) b))))

(print-seq ssquare-prime 1 10)
(newline)
(print-seq coprime-prod 1 10)
