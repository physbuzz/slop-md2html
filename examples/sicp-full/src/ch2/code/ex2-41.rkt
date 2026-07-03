#lang sicp
;; Library functions
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
(define (enumerate-interval low high)
  (if (> low high)
      nil
      (cons low
            (enumerate-interval
             (+ low 1)
             high))))
(define (filter predicate sequence)
  (cond ((null? sequence) nil)
        ((predicate (car sequence))
         (cons (car sequence)
               (filter predicate
                       (cdr sequence))))
        (else  (filter predicate
                       (cdr sequence)))))

;; Solution
;; My solution uses brute force when it doesn't need to (we don't need to
;; generate pairs and then filter) but it's fun to use listy stuff. We've done
;; enough iteration and cons silliness.
(define (tuples n depth)
  (cond ((< n depth) nil)
    ((= depth 1) (map list (enumerate-interval 1 n)))
    (else 
     (append (tuples (- n 1) depth) 
             (map (lambda (arg) (append (list n) arg)) 
                  (tuples (- n 1) (- depth 1)))))))
(define (sum lst) (accumulate (lambda (x y) (+ x y)) 0 lst))
(define (tuples-sum n s depth)
  (define (t-sum? tuple)
    (= s (sum tuple)))
  (filter t-sum? (tuples n depth)))

(tuples 6 3)
(tuples-sum 6 8 3)
