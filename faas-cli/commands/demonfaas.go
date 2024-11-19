package commands

import (
	"fmt"

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
)

func init() {
	d_print("demonfaas init")

	// demonfaasCmd.Flags().IntVarP(&flag1, "flag1", "1", 0, "flag1 test")
	// demonfaasCmd.Flags().BoolVarP(&flag2, "flag2", "2", false, "flag2 test")
	// src, dockerfile, deployment.yaml (already delpoyed stuff to k8)

	demonfaasCmd.Flags().StringVar(&dockerFile, "dockerfile", "", "original input dockerfile")

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
	d_print("pre run")

	d_print(dockerFile)
	return nil
}

func run(cmd *cobra.Command, args []string) error {
	d_print("run")
	return nil
}

func postRun(cmd *cobra.Command, args []string) error {
	d_print("post run")
	return nil
}
