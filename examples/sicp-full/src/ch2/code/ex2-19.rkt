#lang sicp


(define (cc amount coin-values)
  (define no-more? null?)
  (define except-first-denomination cdr)
  (define first-denomination car)
  ;;(define (except-first-denomination lst) (cdr lst))
  (cond ((= amount 0) 
         1)
        ((or (< amount 0) 
             (no-more? coin-values)) 
         0)
        (else
         (+ (cc 
             amount
             (except-first-denomination 
              coin-values))
            (cc 
             (- amount
                (first-denomination 
                 coin-values))
             coin-values)))))
(define us-coins
  (list 50 25 10 5 1))

(define uk-coins
  (list 100 50 20 10 5 2 1 0.5))
(display (cc 100 us-coins))
(newline)
(display (cc 100 uk-coins))
(newline)
(display (cc 100 (list 100 50 20 10 5 2 1 0.5)))
(newline)
(display (cc 100 (list 1 100 0.5 50 5 2 20 10)))
(newline)
(display (cc 100 (list 20 100 10 5 2 1 0.5 50)))
(newline)
(display (cc 100 (list 20 50 10 5 0.5 2 1 100)))
(newline)


