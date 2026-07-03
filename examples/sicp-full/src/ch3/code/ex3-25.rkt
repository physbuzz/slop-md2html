#lang sicp

(define (assoc key records)
  (cond ((null? records) false)
        ((equal? key (caar records))
         (car records))
        (else (assoc key (cdr records)))))

(define (make-table)
  (let ((local-table (list '*table*)))
    (define (lookup . keys)
      (let ((record
             (assoc keys (cdr local-table))))
        (if record (cdr record) false)))
    (define (insert! value . keys)
      (let ((record
             (assoc keys (cdr local-table))))
        (if record
            (set-cdr! record value)
            (set-cdr!
             local-table
             (cons (cons keys value)
                   (cdr local-table)))))
      'ok)
    (define (dispatch m)
      (cond ((eq? m 'lookup-proc) lookup)
            ((eq? m 'insert-proc!) insert!)
            (else (error "Unknown operation:
                          TABLE" m))))
    dispatch))

(define operation-table (make-table))
(define get (operation-table 'lookup-proc))
(define put (operation-table 'insert-proc!))

(put 1 'a 'b)
(put 2 'c 'b)
(put 3 'c 'b 'd 'e)
(display (get 'a 'b)) (newline)
(display (get 'c 'b)) (newline)
(display (get 'c 'b 'd 'e)) (newline)
