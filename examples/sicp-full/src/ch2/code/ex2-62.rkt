#lang sicp

(define (element-of-set? x set)
  (cond ((null? set) false)
        ((= x (car set)) true)
        ((< x (car set)) false)
        (else (element-of-set? x (cdr set)))))

(define (adjoin-set x set)
  (cond ((null? set) (list x))
        ((> x (car set)) 
         (cons (car set) (adjoin-set x (cdr set))))
        ((= x (car set)) set)
        (else (cons x set))))

(define (intersection-set set1 set2)
  (if (or (null? set1) (null? set2))
      '()
      (let ((x1 (car set1)) (x2 (car set2)))
        (cond ((= x1 x2)
               (cons x1 (intersection-set
                         (cdr set1)
                         (cdr set2))))
              ((< x1 x2) (intersection-set
                          (cdr set1)
                          set2))
              ((< x2 x1) (intersection-set
                          set1
                          (cdr set2)))))))

;; set1 is an ordered set, set2 is an ordered set,
;; both with no duplicates
(define (union-set set1 set2)
  (cond ((null? set1) set2)
        ((null? set2) set1)
        (else (let ((x1 (car set1)) (x2 (car set2)))
          (cond ((= x1 x2)
                 (cons x1 (union-set
                           (cdr set1)
                           (cdr set2))))
                ((< x1 x2) 
                 (cons x1 (union-set 
                            (cdr set1)
                            set2)))
                ((< x2 x1) 
                 (cons x2 (union-set
                            set1
                            (cdr set2)))))))))

(define set0 (list 0 4 8 12))
(define set1 (list -4 -3 0 1 4))
(define set2 (list 16 18 20))

(intersection-set set0 set1)
(union-set set0 set1)
(union-set set1 set0)
(union-set set1 set2)
(union-set set2 set1)
