#lang sicp
;; Solution
(define (unique-pairs n)
  (define (num-list i m ret)
    (if (= i 0) 
      ret
      (num-list (- i 1) m (cons (list m i) ret))))
  (define (num-list-list m ret)
    (if (> m n)
      ret
      (num-list-list (+ m 1) (append ret (num-list (- m 1) m nil)))))
  (num-list-list 2 nil))
(define (prime-sum-pairs n)
  (filter prime-sum? (unique-pairs n)))

;; Library functions
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
(define (prime-sum? pair)
  (prime? (+ (car pair) (cadr pair))))

(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
(define (filter predicate sequence)
  (cond ((null? sequence) nil)
        ((predicate (car sequence))
         (cons (car sequence)
               (filter predicate
                       (cdr sequence))))
        (else  (filter predicate
                       (cdr sequence)))))

(unique-pairs 5)
(prime-sum-pairs 5)
