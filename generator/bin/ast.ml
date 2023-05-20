(** Defines an AST consisting of should-be-constant-time
    nodes. Nodes include all non-branching arithmetic, 
    logical and comparison operators in C other than '/'
    and '%'. Leafs can be the variable 'x', the variable
    'y', an integer, or a Boolean. *)

type expr =
  (* Input variables *)
  | X
  | Y

  (* Integers *)
  | IntLit of int64

  (* Arithmetic *)
  | Neg of expr
  | Plus of expr * expr
  | Minus of expr * expr
  | Times of expr * expr

  (* Booleans *)
  | True 
  | False

  (* Logical Operators *)
  | Not of expr

  (* Comparison Operators *)
  | LessThan of expr * expr
  | LessEqual of expr * expr
  | GreaterThan of expr * expr
  | GreaterEqual of expr * expr
  | Equal of expr * expr
  | NotEqual of expr * expr

  (* Bitwise Operators *)
  | BitwiseAnd of expr * expr
  | BitwiseOr of expr * expr
  | BitwiseComplement of expr
  | BitwiseXor of expr * expr
  | LeftShift of expr * expr
  | RightShift of expr * expr

let rec string_of_expr = function 
  | X -> "x"
  | Y -> "y"

  | IntLit i -> Int64.to_string i

  | Neg e -> "-" ^ string_of_expr e
  | Plus (e1, e2) -> "(" ^ string_of_expr e1 ^ " + " ^ string_of_expr e2 ^ ")"
  | Minus (e1, e2) -> "(" ^ string_of_expr e1 ^ " - " ^ string_of_expr e2 ^ ")"
  | Times (e1, e2) -> "(" ^ string_of_expr e1 ^ " * " ^ string_of_expr e2 ^ ")"

  | True -> "true"
  | False -> "false"

  | Not e -> "!" ^ string_of_expr e

  | LessThan (e1, e2) -> "(" ^ string_of_expr e1 ^ " < " ^ string_of_expr e2 ^ ")"
  | LessEqual (e1, e2) -> "(" ^ string_of_expr e1 ^ " <= " ^ string_of_expr e2 ^ ")"
  | GreaterThan (e1, e2) -> "(" ^ string_of_expr e1 ^ " > " ^ string_of_expr e2 ^ ")"
  | GreaterEqual (e1, e2) -> "(" ^ string_of_expr e1 ^ " >= " ^ string_of_expr e2 ^ ")"
  | Equal (e1, e2) -> "(" ^ string_of_expr e1 ^ " == " ^ string_of_expr e2 ^ ")"
  | NotEqual (e1, e2) -> "(" ^ string_of_expr e1 ^ " != " ^ string_of_expr e2 ^ ")"

  | BitwiseAnd (e1, e2) -> "(" ^ string_of_expr e1 ^ " & " ^ string_of_expr e2 ^ ")"
  | BitwiseOr (e1, e2) -> "(" ^ string_of_expr e1 ^ " | " ^ string_of_expr e2 ^ ")"
  | BitwiseComplement e -> "~" ^ string_of_expr e
  | BitwiseXor (e1, e2) -> "(" ^ string_of_expr e1 ^ " ^ " ^ string_of_expr e2 ^ ")"
  | LeftShift (e1, e2) -> "(" ^ string_of_expr e1 ^ " << " ^ string_of_expr e2 ^ ")"
  | RightShift (e1, e2) -> "(" ^ string_of_expr e1 ^ " >> " ^ string_of_expr e2 ^ ")"
