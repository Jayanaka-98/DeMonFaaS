// main.go
package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run main.go <filename>")
		return
	}

	filename := os.Args[1]
	cmd := exec.Command("python3", "demon.py", filename)

	output, err := cmd.Output()
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Functions with @DeMonFaaS decorator:\n%s", string(output))
}
