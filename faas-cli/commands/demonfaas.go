package commands

import (
	"bufio"
	"fmt"
	"os"
	"slices"
	"strings"

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
	projectPath       string
	dockerhubUsername string
)

const (
	resultPath = "benchmark-openfaas"
)

var splitProjects = [4]string{"benchmark-app", "benchmark-app-compute", "benchmark-app-data", "benchmark-app-quick"}

func init() {
	d_print("demonfaas init")

	demonfaasCmd.Flags().StringVar(&projectPath, "path", "", "original project path directory")
	demonfaasCmd.Flags().StringVar(&dockerhubUsername, "username", "", "dockerhub username")

	faasCmd.AddCommand(demonfaasCmd)
}

var demonfaasCmd = &cobra.Command{
	Use:      `demonfaas`,
	PreRunE:  preRun,
	RunE:     run,
	PostRunE: postRun,
}

func modifyAndGenerateDockerfile(cmd *cobra.Command, args []string) error {
	excludeWords := []string{"FROM", "CMD", "EXPOSE", "ARG"}

	dockerFileTemplate := `ARG PYTHON_VERSION=3.9
FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/of-watchdog:0.10.4 AS watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} python:${PYTHON_VERSION}-alpine AS build

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

# ---demonfass---
@@@
# ---------------

ENV fprocess="gunicorn app.app:app -b 127.0.0.1:8000"
ENV cgi_headers="true"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:8000"

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]`

	dockerfile := projectPath + "/Dockerfile.kubernetes"

	file, err := os.Open(dockerfile)
	if err != nil {
		return fmt.Errorf("invalid file name")
	}

	defer file.Close()

	scanner := bufio.NewScanner(file)
	payload := ""

	for scanner.Scan() {
		line := scanner.Text()
		words := strings.Fields(line)
		if len(words) == 0 || !slices.Contains(excludeWords, words[0]) {
			payload += (line + "\n")
		}
	}

	newFile := strings.Replace(dockerFileTemplate, "@@@", payload, -1)

	d_print(newFile)

	for _, splitProject := range splitProjects {
		splitFile, err := os.OpenFile(resultPath+"/"+splitProject+"/"+"Dockerfile", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			return fmt.Errorf("invalid file name")
		}
		writer := bufio.NewWriter(splitFile)

		_, err = writer.WriteString(newFile)
		if err != nil {
			return fmt.Errorf("invalid file name")
		}

		err = writer.Flush()
		if err != nil {
			return fmt.Errorf("Error flushing to file")
		}
	}

	return nil
}

func generateStackYaml(cmd *cobra.Command, args []string) error {
	stackTemplate := `provider:
 name: openfaas
 gateway: http://127.0.0.1:8080

functions:
  benchmark-app:
    lang: dockerfile
    handler: ./benchmark-app
    image: @@@/demonfaas-benchmark-app:latest
    route:
  compute:
    lang: dockerfile
    handler: ./benchmark-app-compute
    image: @@@/demonfaas-benchmark-app-compute:latest
  data:
    lang: dockerfile
    handler: ./benchmark-app-data
    image: @@@/demonfaas-benchmark-app-data:latest
  quick:
    lang: dockerfile
    handler: ./benchmark-app-quick
    image: @@@/demonfaas-benchmark-app-quick:latest`

	newStack := strings.Replace(stackTemplate, "@@@", dockerhubUsername, -1)

	file, err := os.OpenFile(resultPath+"/"+"stack.yml", os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0755)
	if err != nil {
		d_print("error opening/creating resultant stack.yaml")
		return fmt.Errorf("invalid file name")
	}

	defer file.Close()

	writer := bufio.NewWriter(file)

	_, err = writer.WriteString(newStack)
	if err != nil {
		return fmt.Errorf("invalid file name")
	}

	err = writer.Flush()
	if err != nil {
		return fmt.Errorf("Error flushing to file")
	}

	return nil
}

func preRun(cmd *cobra.Command, args []string) error {
	d_print("pre run demonfass with dockerfile", projectPath)

	modifyAndGenerateDockerfile(cmd, args)
	generateStackYaml(cmd, args)

	return nil
}

func run(cmd *cobra.Command, args []string) error {
	d_print("run")

	// run the script
	return nil
}

func postRun(cmd *cobra.Command, args []string) error {
	d_print("post run")
	return nil
}
