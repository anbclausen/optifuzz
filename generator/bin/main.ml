open Ast
open Generator
open Write 

let n = 5

let () = 
  Random.self_init ();
  for _ = 0 to n do
    let seed = Random.bits () in
    let distribution = random_distribution seed in
    let ast = random_ast seed 0 distribution in
    let prg = program seed (string_of_expr ast) in
    let filename = (string_of_int seed) ^ ".c" in
    write_file filename prg
  done