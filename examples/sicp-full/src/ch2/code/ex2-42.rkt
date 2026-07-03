#lang sicp

(define (flatmap proc seq)
  (accumulate append nil (map proc seq))) 
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

(define (queens board-size)
  (define empty-board nil)
  (define (last lst) 
    (if (null? (cdr lst)) 
      (car lst) 
      (last (cdr lst))))
  (define (echo x) (display x) x)
  (define (safe? k positions)
    ;(echo positions)
    (define y (last positions))
    (define (safe-loop i rest) 
      (define yprime (car rest))
      (if (= i k)
        #t
        (and (not (= yprime y))
             (not (= (abs (- y yprime)) (abs (- k i))))
             (safe-loop (+ i 1) (cdr rest)))))
    (safe-loop 1 positions))
  (define (adjoin-position new-row k rest-of-queens)
    (append rest-of-queens (list new-row)))
  (define (queen-cols k)
    (if (= k 0)
        (list empty-board)
        (filter
         (lambda (positions) 
           (safe? k positions))
         (flatmap
          (lambda (rest-of-queens)
            (map (lambda (new-row)
                   (adjoin-position 
                    new-row 
                    k 
                    rest-of-queens))
                 (enumerate-interval 
                  1 
                  board-size)))
          (queen-cols (- k 1))))))
  (queen-cols board-size))

(map (lambda (n) (length (queens n))) (enumerate-interval 1 10))
