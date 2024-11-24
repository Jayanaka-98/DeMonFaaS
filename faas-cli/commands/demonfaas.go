package commands

import (
<<<<<<< Updated upstream
	"fmt"
=======
	"bufio"
	"fmt"
	"os"
	"strings"
>>>>>>> Stashed changes

	"github.com/spf13/cobra"
)

const DEBUG = true

func d_print(strs ...interface{}) {
	if !DEBUG {
		return
	}
	fmt.Println(strs...)
}

func d_assert(predicate bool) {
	if !DEBUG {
		return
	}
	if !predicate {
		panic("assertion failed")
	}
}

var (
	dockerFile string
<<<<<<< Updated upstream
=======
	// dockerhubUsername string
>>>>>>> Stashed changes
)

func init() {
	d_print("demonfaas init")

	// demonfaasCmd.Flags().IntVarP(&flag1, "flag1", "1", 0, "flag1 test")
	// demonfaasCmd.Flags().BoolVarP(&flag2, "flag2", "2", false, "flag2 test")
	// src, dockerfile, deployment.yaml (already delpoyed stuff to k8)

	demonfaasCmd.Flags().StringVar(&dockerFile, "dockerfile", "", "original input dockerfile")
<<<<<<< Updated upstream
=======
	// demonfaasCmd.Flags().StringVar(&dockerhubUsername, "username", "", "dockerhub username")

	up, _, _ := faasCmd.Find([]string{"up"})
	demonfaasCmd.Flags().AddFlagSet(up.Flags())
>>>>>>> Stashed changes

	faasCmd.AddCommand(demonfaasCmd)
}

var demonfaasCmd = &cobra.Command{
	Use:      `demonfaas`, // needs to match file name
	Short:    `short fill me in`,
	Long:     `long fill me in`,
	Example:  `example fill me in`,
	PreRunE:  preRun,
	RunE:     run,
	PostRunE: postRun,
}

func preRun(cmd *cobra.Command, args []string) error {
<<<<<<< Updated upstream
	d_print("pre run")

	d_print(dockerFile)
=======
	d_print("pre run demonfass with dockerfile", dockerFile)
	return nil
}

func generateDockerfile(cmd *cobra.Command, args []string) error {
	dockerFileTemplate := `
	ARG PYTHON_VERSION=3.9
	FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/of-watchdog:0.10.4 AS watchdog
	FROM --platform=${TARGETPLATFORM:-linux/amd64} python:${PYTHON_VERSION}-alpine AS build
	
	COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
	RUN chmod +x /usr/bin/fwatchdog
	
	# ---------------
	@@@
	# ---------------
	
	ENV fprocess="gunicorn app.app:app -b 127.0.0.1:8000"
	ENV cgi_headers="true"
	ENV mode="http"
	ENV upstream_url="http://127.0.0.1:8000"
	
	HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1
	
	CMD ["fwatchdog"]
	`

	file, err := os.Open(dockerFile)
	if err != nil {
		return fmt.Errorf("invalid file name")
	}

	defer file.Close()

	scanner := bufio.NewScanner(file)
	payload := ""

	for scanner.Scan() {
		line := scanner.Text()
		if len(line) >= 4 && line[:4] != "FROM" && line[:4] != "CMD " {
			payload += (line + "\n")
		}
	}

	// TODO:
	// make more proper using string formatting
	// parse each line up to first word and create a blacklist for kwargs that should not be added
	new_file := strings.Replace(dockerFileTemplate, "@@@", payload, -1)
	fmt.Println(new_file)

	return nil
}

func generateStackYaml(cmd *cobra.Command, args []string) error {
>>>>>>> Stashed changes
	return nil
}

func run(cmd *cobra.Command, args []string) error {
	d_print("run")
<<<<<<< Updated upstream
=======
	generateDockerfile(cmd, args)
	preRunUp(cmd, args)
	upHandler(cmd, args)
>>>>>>> Stashed changes
	return nil
}

func postRun(cmd *cobra.Command, args []string) error {
	d_print("post run")
	return nil
}
